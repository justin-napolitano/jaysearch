# Agent Error Contract Standards

This bibliography note collects the primary references for machine-readable worker, agent, and platform error contracts.

## Core Error Contract Standard

1. IETF. "RFC 9457: Problem Details for HTTP APIs."
   Link: https://www.rfc-editor.org/rfc/rfc9457

## Design Pattern Reference

2. Cloudflare. "Slashing agent token costs by 98% with RFC 9457-compliant error responses." Published March 11, 2026.
   Link: https://blog.cloudflare.com/rfc-9457-agent-error-pages/

## Supporting Response Formats

3. IANA Media Type Registry. "`application/problem+json`."
   Link: https://www.iana.org/assignments/media-types/application/problem+json

4. Markdown Guide. "Basic Syntax."
   Link: https://www.markdownguide.org/basic-syntax/

## Notes

- RFC 9457 should be treated as the base wire contract for machine-readable execution failures.
- The Cloudflare article is useful as a design reference because it shows how to layer operational extension fields such as retry guidance, escalation guidance, and stable error categories on top of the RFC 9457 base members.
- For this repo, the preferred pattern is:
  - `application/problem+json` for machine handling
  - a markdown rendering of the same semantic payload for terminal operators
  - one semantic contract across both formats
