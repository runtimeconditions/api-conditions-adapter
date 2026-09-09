# api-conditions-adapter
A platform adapter that resolves API conditions using the Backstage API.

Takes a `RuntimeConditionsProfile`'s `kind: api` conditions, resolves each one to the real
service that provides it via the Backstage catalog and Kubernetes integration, and emits a
`CiliumNetworkPolicy` that allows exactly those connections.

## How it works

1. Read a `RuntimeConditionsProfile` from a local file and keep only its `kind: api` conditions.
2. Query Backstage's catalog for all `kind: API` entities
   (`GET /api/catalog/entities/by-query?filter=kind=API`).
3. Parse each entity's `.spec.definition` (an OpenAPI document embedded as a YAML string) and
   match its paths/methods against the profile's declared operations, accounting for path
   parameters (e.g. `{itemId}`).
4. For each match, read the entity's `.relations` for the `apiProvidedBy` targetRef to find the
   Backstage component that actually provides the API.
5. Resolve that component to its real Kubernetes Service via
   `POST /api/kubernetes/resources/workloads/query`. The Kubernetes Service name is not
   guaranteed to match the Backstage component name, so this lookup is required.
6. Emit a `CiliumNetworkPolicy` allowing the source component to reach each resolved
   destination Service, and nothing else.

This tool only generates policy YAML. It does not apply anything to a cluster and does not
run on any kind of trigger or schedule; that is a deliberate next step, not part of this repo yet.

## Installation

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

Requires a reachable Backstage instance (defaults to `http://localhost:7007`, e.g. via
`kubectl -n backstage port-forward svc/backstage 7007:7007`):

```
generate-cnp path/to/profile.yaml
```

Options:

- `--backstage-url` (default `http://localhost:7007`)
- `--namespace` (default `applications`) sets the namespace of the generated policy
- `-o/--output` writes the policy to a file instead of stdout

## Testing

```
pytest
```

Unit tests run fully offline against fixtures captured from a real Backstage catalog
(`tests/fixtures/`), including a decoy API that must not match any condition.
