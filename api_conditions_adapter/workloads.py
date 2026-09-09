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
