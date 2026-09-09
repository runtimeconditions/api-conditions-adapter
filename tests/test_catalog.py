import json
import pathlib

import pytest

from api_conditions_adapter.catalog import (
    matching_entities,
    parse_openapi_operations,
    path_to_pattern,
    provider_ref,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def catalog_apis():
    return json.loads((FIXTURES / "catalog_apis.json").read_text())


def test_path_to_pattern_matches_templated_segment():
    pattern = path_to_pattern("/items/{itemId}/availability")
    assert pattern.match("/items/{itemId}/availability")
    assert not pattern.match("/items/{itemId}/availability/extra")


def test_parse_openapi_operations_extracts_method_and_path(catalog_apis):
    inventory_api = next(e for e in catalog_apis if e["metadata"]["name"] == "inventory-api")
    ops = parse_openapi_operations(inventory_api)
    methods_and_paths = {(m, p.pattern) for m, p in ops}
    assert ("GET", "^/items/[^/]+/availability$") in methods_and_paths
    assert ("POST", "^/reservations$") in methods_and_paths
    assert ("POST", "^/admin/items$") in methods_and_paths


def test_matching_entities_finds_inventory_api_for_availability_condition(catalog_apis):
    condition = {
        "kind": "api",
        "interface": {
            "type": "http",
            "operations": [{"method": "GET", "path": "/items/{itemId}/availability"}],
        },
    }
    matches = matching_entities(condition, catalog_apis)
    names = {m["metadata"]["name"] for m in matches}
    assert names == {"inventory-api"}


def test_matching_entities_excludes_decoy_donor_directory_api(catalog_apis):
    condition = {
        "kind": "api",
        "interface": {
            "type": "http",
            "operations": [{"method": "POST", "path": "/fulfillment-tasks"}],
        },
    }
    matches = matching_entities(condition, catalog_apis)
    names = {m["metadata"]["name"] for m in matches}
    assert names == {"fulfillment-api"}
    assert "donor-directory-api" not in names


def test_provider_ref_reads_api_provided_by_relation(catalog_apis):
    inventory_api = next(e for e in catalog_apis if e["metadata"]["name"] == "inventory-api")
    assert provider_ref(inventory_api) == "component:default/inventory-service"


def test_provider_ref_returns_none_without_relation():
    assert provider_ref({"relations": []}) is None
