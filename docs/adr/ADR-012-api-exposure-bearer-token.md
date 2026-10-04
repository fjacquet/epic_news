# ADR-012: API Exposure With a Mandatory Bearer Token

## Status

Accepted (2026-10-04)

## Context

`POST /kickoff` (`src/epic_news/api.py`) starts a full crew run from a free-text request. Until 3.6.2 it had no authentication or rate limit, bound to `0.0.0.0`, and every compose file published port 8000 on all host interfaces. The request text becomes the agent prompt, and several agents could read local files and reach the web, so anyone who could reach the port could spend LLM credit and steer agents toward reading `/app/.env`.

The endpoint must stay reachable from an external n8n instance (hosted at Hostinger) that triggers runs by webhook. Private-network options were considered and rejected by the project owner: Cloudflare Tunnel and Tailscale will not be used.

## Decision

- `/kickoff` requires `Authorization: Bearer <EPIC_API_TOKEN>`, compared with `hmac.compare_digest`.
- Fail closed: when `EPIC_API_TOKEN` is unset or empty, `/kickoff` answers 503. A missing or wrong token answers 401.
- `user_request` is capped at 2000 characters (422 above).
- At most `EPIC_API_MAX_CONCURRENT` runs (default 1) execute at once; extra requests get 429. The slot is released when the background run ends, whatever the outcome.
- `/health` stays unauthenticated for container health checks.
- Compose publishes the API on `${EPIC_API_BIND:-127.0.0.1}:8000` and Streamlit on `127.0.0.1:8501` only. Streamlit has no authentication and is never exposed.
- When the API must be reached from outside, terminate TLS in front of it (for example Caddy with automatic certificates); the token alone is readable over plain HTTP.
- n8n calls the endpoint with an HTTP Request node and a Header Auth credential (`Authorization` / `Bearer <token>`). Setup: `docs/how-to/expose-api-n8n.md`.

## Consequences

- Every caller must send the token; deployments must set `EPIC_API_TOKEN` before upgrading.
- Default binding is local; exposing the API is an explicit choice (`EPIC_API_BIND=0.0.0.0`) that should come with a TLS proxy.
- A single shared token: no per-caller identity or revocation beyond rotating the value.
- The concurrency cap also bounds LLM spend from a misbehaving caller.
