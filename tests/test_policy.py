from api_conditions_adapter.policy import build_cnp


def test_build_cnp_shape():
    destinations = [
        {"name": "stock-provider-v2", "namespace": "applications", "port": 8080},
        {"name": "dispatch-planner-v1", "namespace": "applications", "port": 8080},
    ]
    cnp = build_cnp("request-coordinator", "applications", destinations)

    assert cnp["kind"] == "CiliumNetworkPolicy"
    assert cnp["metadata"]["name"] == "request-coordinator-generated-egress"
    assert cnp["metadata"]["namespace"] == "applications"
    assert cnp["spec"]["endpointSelector"]["matchLabels"] == {
        "backstage.io/kubernetes-id": "request-coordinator"
    }
    assert len(cnp["spec"]["egress"]) == 2
    service_names = {
        rule["toServices"][0]["k8sService"]["serviceName"] for rule in cnp["spec"]["egress"]
    }
    assert service_names == {"stock-provider-v2", "dispatch-planner-v1"}
    for rule in cnp["spec"]["egress"]:
        assert rule["toPorts"][0]["ports"][0] == {"port": "8080", "protocol": "TCP"}
