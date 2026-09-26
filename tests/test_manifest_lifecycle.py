from datetime import UTC, datetime

from rj_energy.lifecycle.manifest import (
    append_entry,
    apply_gate_decision,
    detect_revision,
    empty_manifest,
    evaluate_gate,
    find_existing,
)
from rj_energy.models import LifecycleStatus, RawFileRecord, ValidationOutcome


def _record(hash_value: str, reference_period: str = "2026-06") -> RawFileRecord:
    return RawFileRecord(
        source="ons",
        dataset="carga_verificada",
        resource_id="ons-RJ-2026-06",
        resource_name="carga_verificada_RJ_2026-06",
        reference_period=reference_period,
        format="json",
        download_url="https://example.org/x",
        local_path="/tmp/x.json",
        retrieved_at=datetime.now(UTC).isoformat(),
        hash_sha256=hash_value,
        file_size=100,
    )


def test_append_entry_and_find_existing():
    manifest = empty_manifest()
    manifest = append_entry(manifest, _record("hash1"))

    assert manifest.height == 1
    found = find_existing(manifest, "ons", "ons-RJ-2026-06", "hash1")
    assert found.height == 1

    not_found = find_existing(manifest, "ons", "ons-RJ-2026-06", "hash-other")
    assert not_found.is_empty()


def test_append_entry_demotes_previous_latest():
    manifest = empty_manifest()
    manifest = append_entry(manifest, _record("hash1"))
    manifest = append_entry(manifest, _record("hash2"))

    latest = manifest.filter(manifest["is_latest_downloaded"])
    assert latest.height == 1
    assert latest.row(0, named=True)["hash_sha256"] == "hash2"


def test_detect_revision_when_hash_changes():
    manifest = empty_manifest()
    manifest = append_entry(manifest, _record("hash1"))

    old_hash = detect_revision(manifest, "ons", "ons-RJ-2026-06", "2026-06", "hash2")
    assert old_hash == "hash1"

    same_hash = detect_revision(manifest, "ons", "ons-RJ-2026-06", "2026-06", "hash1")
    assert same_hash is None


def test_gate_approves_and_promotes():
    manifest = empty_manifest()
    manifest = append_entry(manifest, _record("hash1"))

    outcomes = [ValidationOutcome(check_name="schema", passed=True, severity="error", details="ok")]
    decision = evaluate_gate("ons-RJ-2026-06", "2026-06", outcomes)
    assert decision.approved

    manifest = apply_gate_decision(manifest, decision)
    row = manifest.row(0, named=True)
    assert row["lifecycle_status"] == LifecycleStatus.ACTIVE.value
    assert row["is_active_for_gold"] is True


def test_gate_rejects_and_quarantines_without_removing_previous_active():
    manifest = empty_manifest()
    manifest = append_entry(manifest, _record("hash1"))
    ok_outcomes = [ValidationOutcome(check_name="schema", passed=True, severity="error", details="ok")]
    manifest = apply_gate_decision(manifest, evaluate_gate("ons-RJ-2026-06", "2026-06", ok_outcomes))

    bad_record = _record("hash2")
    bad_record = bad_record.model_copy(update={"resource_id": "ons-RJ-2026-06-v2"})
    manifest = append_entry(manifest, bad_record)

    bad_outcomes = [ValidationOutcome(check_name="schema", passed=False, severity="error", details="schema quebrado")]
    decision = evaluate_gate("ons-RJ-2026-06-v2", "2026-06", bad_outcomes)
    assert not decision.approved

    manifest = apply_gate_decision(manifest, decision)

    quarantined = manifest.filter(manifest["resource_id"] == "ons-RJ-2026-06-v2").row(0, named=True)
    assert quarantined["lifecycle_status"] == LifecycleStatus.QUARANTINED.value

    # A versão anterior continua ativa na GOLD.
    previous = manifest.filter(manifest["resource_id"] == "ons-RJ-2026-06").row(0, named=True)
    assert previous["is_active_for_gold"] is True
