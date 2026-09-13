from .catalog import path_to_pattern


def build_cnp(source_name, source_selector, namespace, destinations):
    return {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumNetworkPolicy",
        "metadata": {
            "name": f"{source_name}-generated-egress",
            "namespace": namespace,
        },
        "spec": {
            "endpointSelector": {"matchLabels": source_selector},
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
                        {
                            "ports": [{"port": str(dest["port"]), "protocol": "TCP"}],
                            "rules": {
                                "http": [
                                    {
                                        "method": op["method"].upper(),
                                        "path": path_to_pattern(op["path"]).pattern,
                                    }
                                    for op in dest["operations"]
                                ]
                            },
                        }
                    ],
                }
                for dest in destinations
            ],
        },
    }
