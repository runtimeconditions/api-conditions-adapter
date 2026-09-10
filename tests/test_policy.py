from api_conditions_adapter.policy import build_cnp


def test_build_cnp_shape():
    destinations = [
        {
            "name": "stock-provider-v2",
            "namespace": "applications",
            "port": 8080,
            "operations": [{"method": "GET", "path": "/items/{itemId}/availability"}],
        },
        {
            "name": "dispatch-planner-v1",
            "namespace": "applications",
            "port": 8080,
            "operations": [{"method": "POST", "path": "/fulfillment-tasks"}],
        },
    ]
    source_selector = {"backstage.io/kubernetes-id": "federal-request-coordinator"}
    cnp = build_cnp("request-coordinator", source_selector, "applications", destinations)

    assert cnp["kind"] == "CiliumNetworkPolicy"
    assert cnp["metadata"]["name"] == "request-coordinator-generated-egress"
    assert cnp["metadata"]["namespace"] == "applications"
    assert cnp["spec"]["endpointSelector"]["matchLabels"] == source_selector
    assert len(cnp["spec"]["egress"]) == 2
    service_names = {
        rule["toServices"][0]["k8sService"]["serviceName"] for rule in cnp["spec"]["egress"]
    }
    assert service_names == {"stock-provider-v2", "dispatch-planner-v1"}
    for rule in cnp["spec"]["egress"]:
        assert rule["toPorts"][0]["ports"][0] == {"port": "8080", "protocol": "TCP"}

    inventory_rule = next(
        r
        for r in cnp["spec"]["egress"]
        if r["toServices"][0]["k8sService"]["serviceName"] == "stock-provider-v2"
    )
    assert inventory_rule["toPorts"][0]["rules"]["http"] == [
        {"method": "GET", "path": "^/items/[^/]+/availability$"}
    ]
