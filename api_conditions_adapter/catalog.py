import re

import requests
import yaml

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def fetch_api_entities(backstage_url, session=None):
    session = session or requests
    resp = session.get(
        f"{backstage_url}/api/catalog/entities/by-query",
        params={"filter": "kind=API"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["items"]


def path_to_pattern(path):
    escaped = re.escape(path)
    templated = re.sub(r"\\\{[^}]+\\\}", "[^/]+", escaped)
    return re.compile(f"^{templated}$")


def parse_openapi_operations(entity):
    definition = yaml.safe_load(entity["spec"]["definition"])
    operations = []
    for path, methods in (definition.get("paths") or {}).items():
        for method in methods:
            if method.upper() in HTTP_METHODS:
                operations.append((method.upper(), path_to_pattern(path)))
    return operations


def matching_entities(condition, api_entities):
    matches = []
    for op in condition["interface"]["operations"]:
        wanted_method = op["method"].upper()
        wanted_path = op["path"]
        for entity in api_entities:
            for method, pattern in parse_openapi_operations(entity):
                if method == wanted_method and pattern.match(wanted_path):
                    matches.append(entity)
                    break
    return matches


def provider_ref(entity):
    for rel in entity.get("relations", []):
        if rel.get("type") == "apiProvidedBy":
            return rel["targetRef"]
    return None
