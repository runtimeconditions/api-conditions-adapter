import re

import requests
import yaml

HTTP_METHODS = {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"}


def fetch_api_entities(backstage_url, session=None):
    session = session or requests
    items = []
    params = {"filter": "kind=API"}
    while True:
        resp = session.get(
            f"{backstage_url}/api/catalog/entities/by-query", params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        items.extend(data["items"])
        cursor = data.get("pageInfo", {}).get("nextCursor")
        if not cursor:
            return items
        params = {"cursor": cursor}


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
                    matches.append((entity, op))
                    break
    return matches


def provider_ref(entity):
    for rel in entity.get("relations", []):
        if rel.get("type") == "apiProvidedBy":
            return rel["targetRef"]
    return None
