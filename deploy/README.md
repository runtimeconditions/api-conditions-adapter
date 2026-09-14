# Kratix integration

Install Kratix (single-cluster quick start):

```
kubectl apply -f https://github.com/syntasso/kratix/releases/download/latest/kratix-quick-start-installer.yaml
kubectl logs -f job/kratix-quick-start-installer -n default
```

This registers the cluster itself as a Destination labelled `environment: dev`, which is what
`promise.yaml`'s `destinationSelectors` targets.

Install the Promise:

```
kubectl apply -f deploy/promise.yaml
```

This installs the `RuntimeConditionsProfile` CRD (embedded under `spec.api`, taken from
[runtime-conditions-crd](https://github.com/runtimeconditions/runtime-conditions-crd)) and
registers a resource workflow whose pipeline container is this repo's image, published to GHCR.

The embedded CRD adds `maxItems`/`maxLength` bounds to the `conditions` and `extensions`
fields that aren't in the upstream CRD as of this writing. Without them, the CEL validation
rules on those fields exceed Kubernetes' cost budget and the CRD is rejected outright, this
reproduces with `runtime-conditions-crd`'s own generated CRD YAML applied directly, so it's
an upstream issue, not something specific to Kratix.

Trigger it:

```
kubectl apply -f deploy/sample-request-coordinator.yaml
```

Kratix runs the pipeline container, mounting the created resource at
`/kratix/input/object.yaml` and reading anything the container writes to `/kratix/output/` back
onto the cluster. The image's entrypoint runs `generate-cnp` against those paths, using
`BACKSTAGE_URL` for cluster-internal access to Backstage, so the resulting
`CiliumNetworkPolicy` is applied with no extra code beyond what's already in this repo.

Check the result:

```
kubectl -n applications get ciliumnetworkpolicy request-coordinator-generated-egress
```
