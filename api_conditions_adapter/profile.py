import yaml


def load_profile(path):
    with open(path) as f:
        return yaml.safe_load(f)


def api_conditions(profile):
    return [c for c in profile.get("conditions", []) if c.get("kind") == "api"]


def source_component_name(profile):
    return profile["metadata"]["name"]
