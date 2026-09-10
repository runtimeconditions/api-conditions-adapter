import json
import pathlib

import pytest

from api_conditions_adapter.catalog import (
    HTTP_METHODS,
    fetch_api_entities,
    matching_entities,
    parse_openapi_operations,
    path_to_pattern,
    provider_ref,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def catalog_apis():
    return json.loads((FIXTURES / "catalog_apis.json").read_text())


def test_http_methods_matches_common_integrations_extension():
    assert HTTP_METHODS == {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"}


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
    op = {"method": "GET", "path": "/items/{itemId}/availability"}
    condition = {"kind": "api", "interface": {"type": "http", "operations": [op]}}
    matches = matching_entities(condition, catalog_apis)
    assert [(e["metadata"]["name"], matched_op) for e, matched_op in matches] == [
        ("inventory-api", op)
    ]


def test_matching_entities_excludes_decoy_donor_directory_api(catalog_apis):
    op = {"method": "POST", "path": "/fulfillment-tasks"}
    condition = {"kind": "api", "interface": {"type": "http", "operations": [op]}}
    matches = matching_entities(condition, catalog_apis)
    names = {e["metadata"]["name"] for e, _ in matches}
    assert names == {"fulfillment-api"}
    assert "donor-directory-api" not in names


def test_provider_ref_reads_api_provided_by_relation(catalog_apis):
    inventory_api = next(e for e in catalog_apis if e["metadata"]["name"] == "inventory-api")
    assert provider_ref(inventory_api) == "component:default/inventory-service"


def test_provider_ref_returns_none_without_relation():
    assert provider_ref({"relations": []}) is None


def test_fetch_api_entities_follows_next_cursor():
    pages = [
        {"items": [{"metadata": {"name": "a"}}], "pageInfo": {"nextCursor": "page2"}},
        {"items": [{"metadata": {"name": "b"}}], "pageInfo": {}},
    ]
    requested_params = []

    class FakeResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    class FakeSession:
        def get(self, url, params, timeout):
            requested_params.append(params)
            return FakeResponse(pages[len(requested_params) - 1])

    entities = fetch_api_entities("http://backstage", session=FakeSession())
    assert [e["metadata"]["name"] for e in entities] == ["a", "b"]
    assert requested_params == [{"filter": "kind=API"}, {"cursor": "page2"}]
