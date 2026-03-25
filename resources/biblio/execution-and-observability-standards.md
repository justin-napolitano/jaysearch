# Execution And Observability Standards

This bibliography note collects the most relevant standards and primary references for a terminal-first governed worker system with pluggable local or cloud executors.

## Packaging and Runtime

1. Open Container Initiative. "OCI Image Format Specification."
   Link: https://github.com/opencontainers/image-spec

2. Open Container Initiative. "OCI Runtime Specification."
   Link: https://github.com/opencontainers/runtime-spec

3. Open Container Initiative.
   Link: https://opencontainers.org/

## Event Envelopes

4. Cloud Native Computing Foundation. "CloudEvents."
   Link: https://cloudevents.io/

5. CNCF. "CloudEvents Project."
   Link: https://www.cncf.io/projects/cloudevents/

## Telemetry and Correlation

6. OpenTelemetry. "Logs Data Model and Logs Specifications."
   Link: https://opentelemetry.io/docs/specs/otel/logs/

7. OpenTelemetry. "Semantic Conventions."
   Link: https://opentelemetry.io/docs/specs/semconv/

8. W3C. "Trace Context."
   Link: https://www.w3.org/TR/trace-context/

## Lineage and Run Metadata

9. OpenLineage. "OpenLineage Object Model."
   Link: https://openlineage.io/docs/1.37.0/spec/object-model/

10. OpenLineage project.
    Link: https://openlineage.io/

## Dynamic Runtime Pattern References

11. Cloudflare. "Dynamic Workers."
    Link: https://developers.cloudflare.com/dynamic-workers/

12. Cloudflare. "Workers Runtime APIs."
    Link: https://developers.cloudflare.com/workers/runtime-apis/

13. Cloudflare. "Workers Observability."
    Link: https://developers.cloudflare.com/workers/observability/

## Notes

- No single standard covers the full kernel-plus-worker model proposed in this repo.
- The strongest standards stack currently looks like:
  - OCI for executor packaging where containers are used
  - CloudEvents for lifecycle event envelopes
  - OpenTelemetry plus W3C Trace Context for telemetry and correlation
  - OpenLineage as inspiration for run and artifact lineage, not as a forced canonical model
- Dynamic Workers is a design-pattern reference for sandboxed on-demand execution, not a direct standard.
