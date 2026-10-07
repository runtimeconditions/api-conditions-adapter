import json
import pathlib

import yaml

from api_conditions_adapter import cli

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_main_generates_cnp_from_profile(monkeypatch, capsys):
    catalog_apis = json.loads((FIXTURES / "catalog_apis.json").read_text())
    workloads_by_ref = {
        "component:default/request-coordinator": json.loads(
            (FIXTURES / "workloads_request_coordinator.json").read_text()
        ),
        "component:default/inventory-service": json.loads(
            (FIXTURES / "workloads_inventory_service.json").read_text()
        ),
        "component:default/fulfillment-service": json.loads(
            (FIXTURES / "workloads_fulfillment_service.json").read_text()
        ),
    }

    monkeypatch.setattr(cli, "fetch_api_entities", lambda backstage_url: catalog_apis)

    def fake_fetch_workloads(backstage_url, entity_ref):
        return workloads_by_ref[entity_ref]

    monkeypatch.setattr(cli, "fetch_workloads", fake_fetch_workloads)
    monkeypatch.setattr(cli, "post_fulfillments", lambda *a, **k: None)

    exit_code = cli.main([str(FIXTURES / "request-coordinator.yaml")])
    assert exit_code == 0

    output = yaml.safe_load(capsys.readouterr().out)
    assert output["metadata"]["name"] == "request-coordinator-generated-egress"
    assert output["spec"]["endpointSelector"]["matchLabels"] == {
        "backstage.io/kubernetes-id": "request-coordinator"
    }
    service_names = {
        rule["toServices"][0]["k8sService"]["serviceName"] for rule in output["spec"]["egress"]
    }
    assert service_names == {"stock-provider-v2", "dispatch-planner-v1"}


def test_post_fulfillments_posts_one_per_condition():
    cnp = {"metadata": {"name": "request-coordinator-generated-egress", "namespace": "applications"}}
    conditions = [{"name": "available-stock-capability"}, {"name": "delivery-work-capability"}]
    posted = []

    class FakeSession:
        def post(self, url, json, timeout):
            posted.append((url, json))

    cli.post_fulfillments(
        "http://backstage:7007", "request-coordinator", "dev", cnp, conditions, session=FakeSession()
    )

    assert [p[1]["condition"] for p in posted] == [
        "available-stock-capability",
        "delivery-work-capability",
    ]
    assert all(p[1]["resources"][0]["reference"] == "applications/request-coordinator-generated-egress" for p in posted)
