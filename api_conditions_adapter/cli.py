import argparse
import sys

import yaml

from .catalog import fetch_api_entities, matching_entities, provider_ref
from .policy import build_cnp
from .profile import api_conditions, load_profile, source_component_name
from .workloads import extract_selector, extract_service, fetch_workloads


def resolve_destinations(profile, backstage_url):
    api_entities = fetch_api_entities(backstage_url)

    ops_by_ref = {}
    for condition in api_conditions(profile):
        for entity, op in matching_entities(condition, api_entities):
            ref = provider_ref(entity)
            if ref:
                ops_by_ref.setdefault(ref, []).append(op)

    destinations = []
    for ref, ops in ops_by_ref.items():
        service = extract_service(fetch_workloads(backstage_url, ref))
        if service:
            service["operations"] = ops
            destinations.append(service)
    return destinations


def resolve_source(profile, backstage_url, source_ref):
    ref = source_ref or f"component:default/{source_component_name(profile)}"
    return extract_selector(fetch_workloads(backstage_url, ref))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a CiliumNetworkPolicy from a RuntimeConditionsProfile's api conditions."
    )
    parser.add_argument("profile_path")
    parser.add_argument("--backstage-url", default="http://localhost:7007")
    parser.add_argument("--namespace", default="applications")
    parser.add_argument(
        "--source-ref",
        help="Backstage entityRef for the profiled service, "
        "defaults to component:default/<profile name>",
    )
    parser.add_argument("-o", "--output")
    args = parser.parse_args(argv)

    profile = load_profile(args.profile_path)
    source_component = source_component_name(profile)
    source_selector = resolve_source(profile, args.backstage_url, args.source_ref)
    if not source_selector:
        print(f"Could not resolve a Kubernetes selector for {source_component}", file=sys.stderr)
        return 1

    destinations = resolve_destinations(profile, args.backstage_url)
    if not destinations:
        print("No matching APIs found for any api condition in the profile.", file=sys.stderr)
        return 1

    cnp = build_cnp(source_component, source_selector, args.namespace, destinations)
    rendered = yaml.dump(cnp, sort_keys=False)

    if args.output:
        with open(args.output, "w") as f:
            f.write(rendered)
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
