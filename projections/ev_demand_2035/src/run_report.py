#!/usr/bin/env python3
"""Gera todos os artefatos da projeção 2035: cenários anuais (nacional + RJ),
impacto horário na curva de carga real do RJ, e um relatório-resumo em
Markdown. Roda a partir de qualquer diretório:

    python projections/ev_demand_2035/src/run_report.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))

from charging_impact import run_all_strategies
from scenarios import (
    load_assumptions,
    national_light_ev_scenarios,
    pde2035_all_modes_reference,
    rj_ev_scenarios,
    rj_historical_cagr,
    rj_weight_bounds,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULE_ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
REAL_CURVE_PATHS = {"rj": GOLD_DIR / "rj_average_24h.csv", "brasil": GOLD_DIR / "brasil_average_24h.csv"}
OUTPUT_DIR = MODULE_ROOT / "output"

# Impacto horário 2035 em dois casos: central (intermediário, peso central) e
# limite superior de estresse (acelerado, peso alto do RJ) — para não esconder
# o quanto o resultado varia entre o cenário mais provável e o pior caso
# razoável (spec: nunca reportar um número único falsamente preciso quando há
# incerteza real de premissas). O peso do RJ só se aplica à região "rj"; a
# região "brasil" usa a frota nacional diretamente, sem escalonamento.
IMPACT_CASES = {"central": ("intermediario", "central"), "upper_bound": ("acelerado", "high")}


def main() -> int:
    missing = [str(p) for p in REAL_CURVE_PATHS.values() if not p.exists()]
    if missing:
        print(f"Curva(s) real(is) não encontrada(s): {missing} — rode `python -m rj_energy build-gold` no repositório principal primeiro.", file=sys.stderr)
        return 1

    assumptions = load_assumptions()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    national = national_light_ev_scenarios(assumptions)
    national.write_csv(OUTPUT_DIR / "scenarios_national_light_ev.csv")

    rj = rj_ev_scenarios(national, assumptions)
    rj.write_csv(OUTPUT_DIR / "scenarios_rj_light_ev.csv")

    pde_context = pde2035_all_modes_reference(assumptions)
    pde_context.write_csv(OUTPUT_DIR / "context_pde2035_all_modes.csv")

    real_curves = {region: pl.read_csv(path) for region, path in REAL_CURVE_PATHS.items()}

    impact_rows = []
    hourly_frames = []
    n_vehicles_by_region_case: dict[str, dict[str, int]] = {"rj": {}, "brasil": {}}

    for case_label, (scenario_name, weight_case) in IMPACT_CASES.items():
        # Brasil: frota nacional direta (sem peso regional).
        nat_row = national.filter((pl.col("year") == 2035) & (pl.col("scenario") == scenario_name)).row(0, named=True)
        n_vehicles_brasil = int(nat_row["implied_bev_phev_fleet_units"])
        # RJ: frota nacional escalada pelo peso do RJ (baixo/central/alto).
        rj_row = rj.filter(
            (pl.col("year") == 2035) & (pl.col("scenario") == scenario_name) & (pl.col("rj_weight_case") == weight_case)
        ).row(0, named=True)
        n_vehicles_rj = int(rj_row["implied_bev_phev_fleet_units"])

        n_vehicles_by_region_case["brasil"][case_label] = n_vehicles_brasil
        n_vehicles_by_region_case["rj"][case_label] = n_vehicles_rj

        for region, n_vehicles in (("brasil", n_vehicles_brasil), ("rj", n_vehicles_rj)):
            for result in run_all_strategies(real_curves[region], n_vehicles, assumptions):
                impact_rows.append({
                    "region": region,
                    "case": case_label,
                    "scenario": scenario_name,
                    "rj_weight_case": weight_case if region == "rj" else "n/a",
                    "strategy": result.strategy,
                    "n_vehicles": result.n_vehicles,
                    "daily_energy_added_mwh": round(result.daily_energy_added_mwh, 2),
                    "baseline_peak_mw": round(result.baseline_peak_mw, 1),
                    "baseline_peak_hour": result.baseline_peak_hour,
                    "new_peak_mw": round(result.new_peak_mw, 1),
                    "new_peak_hour": result.new_peak_hour,
                    "peak_increase_pct": round(result.peak_increase_pct, 2),
                    "peak_hour_shifted": result.peak_hour_shifted,
                })
                hourly_frames.append(
                    result.hourly.with_columns(
                        pl.lit(region).alias("region"), pl.lit(case_label).alias("case"), pl.lit(result.strategy).alias("strategy")
                    )
                )

    pl.DataFrame(impact_rows).write_csv(OUTPUT_DIR / "grid_impact_summary_2035.csv")
    pl.concat(hourly_frames).write_csv(OUTPUT_DIR / "hourly_load_by_strategy_2035.csv")

    _write_markdown_summary(assumptions, national, rj, pde_context, impact_rows, n_vehicles_by_region_case)
    print(f"Relatórios gerados em {OUTPUT_DIR}")
    return 0


def _write_markdown_summary(
    assumptions: dict,
    national: pl.DataFrame,
    rj: pl.DataFrame,
    pde_context: pl.DataFrame,
    impact_rows: list[dict],
    n_vehicles_by_region_case: dict[str, dict[str, int]],
) -> None:
    weight_low, weight_high = rj_weight_bounds(assumptions)
    cagr = rj_historical_cagr(assumptions)

    nat_2035 = {r["scenario"]: r for r in national.filter(pl.col("year") == 2035).iter_rows(named=True)}
    pde_2035 = pde_context.filter(pl.col("year") == 2035).row(0, named=True)
    official_fleet_2035 = assumptions["national_ev"]["fleet_light_2035_units_reference"]
    accelerated_implied_fleet = nat_2035["acelerado"]["implied_bev_phev_fleet_units"]
    consistency_ratio = accelerated_implied_fleet / official_fleet_2035

    lines = [
        "# Resumo executivo — Projeção de Demanda Elétrica por Eletrificação Veicular (2035)",
        "",
        f"_Gerado em {datetime.now(UTC).isoformat()}. Ver `README.md` deste módulo para metodologia completa e `research/` para as fontes primárias._",
        "",
        "## Cenários nacionais — demanda de recarga de veículos leves (BEV+PHEV), 2035",
        "",
        "| Cenário | Demanda (TWh) | Frota implícita (BEV+PHEV) |",
        "|---|---|---|",
    ]
    for scenario in ("conservador", "intermediario", "acelerado"):
        r = nat_2035[scenario]
        lines.append(f"| {scenario} | {r['demand_light_ev_twh']:.2f} | {r['implied_bev_phev_fleet_units']:,} |")

    lines += [
        "",
        (
            "Para contexto (não comparável diretamente — escopo mais amplo, todos os modais): "
            f"o PDE 2035 da EPE projeta **{pde_2035['demand_all_modes_twh']:.2f} TWh** em 2035 para "
            "TODA a eletromobilidade (leves + ônibus + caminhões), partindo de 0,627 TWh em 2025."
        ),
        "",
        (
            "**Checagem de consistência**: a frota implícita do cenário acelerado em 2035 "
            f"({accelerated_implied_fleet:,.0f} veículos BEV+PHEV, derivada da energia) equivale a "
            f"**{consistency_ratio:.0%}** da frota oficial de leves eletrificados projetada pela EPE para 2035 "
            f"({official_fleet_2035:,} veículos, PDE 2035 — inclui também HEV não-plugável). Como HEV não consome "
            "eletricidade da rede, esperar uma fração menor que 100% é o resultado esperado, não um erro do modelo."
        ),
        "",
        "## Rio de Janeiro (derivado proporcionalmente — sem projeção estadual publicada)",
        "",
        (
            f"Peso do RJ na frota nacional de BEV+PHEV: **{weight_low:.1%} a {weight_high:.1%}** "
            "(faixa por ambiguidade de escopo entre fontes — ver README)."
        ),
        (
            f"CAGR histórico observado da frota do próprio RJ (2021-2025, Detran-RJ): **{cagr:.0%} a.a.** "
            "— explosivo por partir de base baixa; NÃO extrapolado linearmente até 2035 (ver README)."
        ),
        "",
        "| Cenário | Peso RJ | Demanda RJ 2035 (TWh) | Frota implícita RJ 2035 |",
        "|---|---|---|---|",
    ]
    for scenario in ("conservador", "intermediario", "acelerado"):
        for weight_case in ("low", "central", "high"):
            row = rj.filter(
                (pl.col("year") == 2035) & (pl.col("scenario") == scenario) & (pl.col("rj_weight_case") == weight_case)
            ).row(0, named=True)
            lines.append(
                f"| {scenario} | {weight_case} | {row['demand_light_ev_twh']:.4f} | {row['implied_bev_phev_fleet_units']:,} |"
            )

    region_titles = {"brasil": "Brasil (curva nacional real: soma dos 4 subsistemas ONS — S+NE+N+SECO)", "rj": "Rio de Janeiro (curva real observada, área ONS RJ)"}
    for region in ("brasil", "rj"):
        n_by_case = n_vehicles_by_region_case[region]
        lines += [
            "",
            f"## Impacto na curva de carga real — {region_titles[region]} — 2035",
            "",
            (
                f"Curva base: `data/gold/{region}_average_24h.csv` (observada, coletada do ONS por este mesmo datalake). "
                "Dois casos: **central** (cenário intermediário" + (", peso RJ central" if region == "rj" else "") + " — resultado mais provável) e "
                "**upper_bound** (cenário acelerado" + (", peso RJ alto" if region == "rj" else "") + " — pior caso razoável). Frota usada: "
                f"central={n_by_case['central']:,} veículos, upper_bound={n_by_case['upper_bound']:,} veículos."
            ),
            "",
            "| Caso | Estratégia | Pico base (MW) | Hora pico base | Novo pico (MW) | Nova hora pico | Aumento do pico (%) | Pico mudou de hora? |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for row in impact_rows:
            if row["region"] != region:
                continue
            lines.append(
                f"| {row['case']} | {row['strategy']} | {row['baseline_peak_mw']:.0f} | {row['baseline_peak_hour']}h | "
                f"{row['new_peak_mw']:.0f} | {row['new_peak_hour']}h | {row['peak_increase_pct']:.2f}% | "
                f"{'sim' if row['peak_hour_shifted'] else 'não'} |"
            )

    lines += [
        "",
        (
            "**Leitura**: tanto o pico real observado do sistema RJ quanto o do Brasil (soma dos 4 subsistemas) "
            "ocorrem às 19h — exatamente dentro da janela em que a pesquisa (NREL 2021; tarifa de ponta Light-RJ, "
            "17h30-20h30) aponta como o horário típico de conexão residencial de VEs. Carregamento não controlado "
            "tende a empilhar-se sobre o pico já existente; o carregamento inteligente (preenchimento de vale) e o "
            "deslocamento para a madrugada (ex.: piloto Copel Mobiflex, 00h-06h) reduzem ou eliminam esse efeito."
        ),
        "",
    ]

    (OUTPUT_DIR / "RESUMO_EXECUTIVO.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
