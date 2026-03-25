# Token Economy And API-First Execution

This bibliography note collects the standards and design references most relevant to compact, API-centric agent execution surfaces.

## API Discovery And Contract Surfaces

1. OpenAPI Initiative. "OpenAPI Specification."
   Link: https://spec.openapis.org/oas/

2. OpenAPI Initiative. "OpenAPI Specification v3.1.2."
   Link: https://spec.openapis.org/oas/v3.1.2.html

## MCP And Capability Negotiation

3. Model Context Protocol. "Specification Overview." Protocol Revision 2025-06-18.
   Link: https://modelcontextprotocol.io/specification/2025-06-18/basic

4. Model Context Protocol. "Versioning."
   Link: https://modelcontextprotocol.io/specification/

## Token-Efficient Tooling Pattern References

5. Cloudflare. "Code Mode: give agents an entire API in 1,000 tokens." Published 2026-02-20.
   Link: https://blog.cloudflare.com/code-mode-mcp/

## Notes

- OpenAPI is the strongest standards reference for compact API discovery and code generation against bounded typed surfaces.
- MCP is useful for interoperability and capability negotiation, but it should not force large static tool catalogs into the model context when a cheaper bounded code surface can serve the same task.
- Cloudflare's Code Mode pattern is a strong design reference because it keeps the exposed tool surface nearly fixed while letting the model discover and compose capabilities through code.
- For this repo, the preferred default should be:
  - canonical repo-native APIs and contracts
  - bounded code generation against those APIs
  - skills or MCP servers only where they add clear value without materially inflating context cost
