def build_cnp(source_component, namespace, destinations):
    return {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumNetworkPolicy",
        "metadata": {
            "name": f"{source_component}-generated-egress",
            "namespace": namespace,
        },
        "spec": {
            "endpointSelector": {
                "matchLabels": {"backstage.io/kubernetes-id": source_component}
            },
            "egress": [
                {
                    "toServices": [
                        {
                            "k8sService": {
                                "serviceName": dest["name"],
                                "namespace": dest["namespace"],
                            }
                        }
                    ],
                    "toPorts": [
                        {"ports": [{"port": str(dest["port"]), "protocol": "TCP"}]}
                    ],
                }
                for dest in destinations
            ],
        },
    }
