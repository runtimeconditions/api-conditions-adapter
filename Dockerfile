FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY api_conditions_adapter ./api_conditions_adapter
RUN pip install --no-cache-dir .
ENTRYPOINT ["sh", "-c", "generate-cnp /kratix/input/object.yaml --backstage-url \"$BACKSTAGE_URL\" -o /kratix/output/cilium-network-policy.yaml"]
