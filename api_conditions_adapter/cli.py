import argparse
import sys

import yaml

from .catalog import fetch_api_entities, matching_entities, provider_ref
from .policy import build_cnp
from .profile import api_conditions, load_profile, source_component_name
from .workloads import extract_service, fetch_workloads


def resolve_destinations(profile, backstage_url):
    api_entities = fetch_api_entities(backstage_url)

    seen_refs = set()
    destinations = []
    for condition in api_conditions(profile):
        for entity in matching_entities(condition, api_entities):
            ref = provider_ref(entity)
            if not ref or ref in seen_refs:
                continue
            seen_refs.add(ref)
            workloads = fetch_workloads(backstage_url, ref)
            service = extract_service(workloads)
            if service:
                destinations.append(service)
    return destinations


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a CiliumNetworkPolicy from a RuntimeConditionsProfile's api conditions."
    )
    parser.add_argument("profile_path")
    parser.add_argument("--backstage-url", default="http://localhost:7007")
    parser.add_argument("--namespace", default="applications")
    parser.add_argument("-o", "--output")
    args = parser.parse_args(argv)

    profile = load_profile(args.profile_path)
    source_component = source_component_name(profile)
    destinations = resolve_destinations(profile, args.backstage_url)

    if not destinations:
        print("No matching APIs found for any api condition in the profile.", file=sys.stderr)
        return 1

    cnp = build_cnp(source_component, args.namespace, destinations)
    rendered = yaml.dump(cnp, sort_keys=False)

    if args.output:
        with open(args.output, "w") as f:
            f.write(rendered)
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
