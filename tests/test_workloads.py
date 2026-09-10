import json
import pathlib

from api_conditions_adapter.workloads import extract_selector, extract_service

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_extract_service_returns_name_namespace_port():
    response = json.loads((FIXTURES / "workloads_inventory_service.json").read_text())
    service = extract_service(response)
    assert service == {"name": "stock-provider-v2", "namespace": "applications", "port": 8080}


def test_extract_service_returns_none_when_no_services_present():
    assert extract_service({"items": [{"resources": []}]}) is None


def test_extract_selector_reads_actual_pod_label():
    response = json.loads((FIXTURES / "workloads_inventory_service.json").read_text())
    assert extract_selector(response) == {"backstage.io/kubernetes-id": "inventory-service"}


def test_extract_selector_returns_none_when_no_pods_present():
    assert extract_selector({"items": [{"resources": []}]}) is None
