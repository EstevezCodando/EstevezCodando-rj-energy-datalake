import json

import pytest

from rj_energy.config import load_config
from rj_energy.discovery.ckan import (
    discover_package_resources,
    select_preferred_resource,
)
from rj_energy.utils.http import PipelineHttpClient


@pytest.fixture
def http_client() -> PipelineHttpClient:
    client = PipelineHttpClient.create(load_config())
    yield client
    client.close()


def test_discover_package_resources(httpx_mock, fixtures_dir, http_client):
    payload = json.loads((fixtures_dir / "ckan_package_show_sample.json").read_text())
    httpx_mock.add_response(url="https://example.org/api/3/action/package_show?id=abc", json=payload)

    resources = discover_package_resources(http_client, "https://example.org/api/3/action/package_show?id=abc", dataset="aneel_ctr")

    assert len(resources) == 3
    assert {r.format for r in resources} == {"csv", "parquet"}
    assert resources[0].package_id == "2594ebad-1306-49d1-9f30-ded144acca87"


def test_select_preferred_resource_prefers_parquet(httpx_mock, fixtures_dir, http_client):
    payload = json.loads((fixtures_dir / "ckan_package_show_sample.json").read_text())
    httpx_mock.add_response(url="https://example.org/api/3/action/package_show?id=abc", json=payload)
    resources = discover_package_resources(http_client, "https://example.org/api/3/action/package_show?id=abc", dataset="aneel_ctr")

    picked = select_preferred_resource(resources, ["parquet", "csv"], name_filter="consumidor")
    assert picked is not None
    assert picked.format == "parquet"


def test_select_preferred_resource_filters_by_name(httpx_mock, fixtures_dir, http_client):
    payload = json.loads((fixtures_dir / "ckan_package_show_sample.json").read_text())
    httpx_mock.add_response(url="https://example.org/api/3/action/package_show?id=abc", json=payload)
    resources = discover_package_resources(http_client, "https://example.org/api/3/action/package_show?id=abc", dataset="aneel_ctr")

    picked = select_preferred_resource(resources, ["parquet", "csv"], name_filter="redes")
    assert picked is not None
    assert "Redes" in picked.name
