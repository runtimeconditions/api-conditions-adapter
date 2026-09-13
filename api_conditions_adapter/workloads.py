import requests


def fetch_workloads(backstage_url, entity_ref, session=None):
    session = session or requests
    resp = session.post(
        f"{backstage_url}/api/kubernetes/resources/workloads/query",
        json={"entityRef": entity_ref, "auth": {}},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def extract_selector(workloads_response, label_key="backstage.io/kubernetes-id"):
    for item in workloads_response.get("items", []):
        for group in item.get("resources", []):
            if group.get("type") == "pods" and group.get("resources"):
                labels = group["resources"][0]["metadata"].get("labels", {})
                if label_key in labels:
                    return {label_key: labels[label_key]}
    return None


def extract_service(workloads_response):
    for item in workloads_response.get("items", []):
        for group in item.get("resources", []):
            if group.get("type") == "services" and group.get("resources"):
                svc = group["resources"][0]
                return {
                    "name": svc["metadata"]["name"],
                    "namespace": svc["metadata"]["namespace"],
                    "port": svc["spec"]["ports"][0]["port"],
                }
    return None
