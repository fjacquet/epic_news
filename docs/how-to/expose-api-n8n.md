# Expose the API to n8n

This guide shows how to let an [n8n](https://n8n.io) workflow trigger Epic News
crews through `POST /kickoff` without leaving the API open to anyone.

## How the API is protected

- `POST /kickoff` requires the header `Authorization: Bearer <token>`. The token
  is compared with the `EPIC_API_TOKEN` environment variable.
- If `EPIC_API_TOKEN` is unset or empty, `/kickoff` answers **503** for every
  request: the API fails closed instead of running unauthenticated.
- A missing or wrong token gets **401**.
- `user_request` is limited to 2000 characters (longer requests get **422**).
- Only `EPIC_API_MAX_CONCURRENT` kickoffs (default `1`) run at once. Extra
  requests get **429** until a running crew finishes; retry later.
- `GET /health` stays unauthenticated for container health checks.
- Docker Compose publishes the API port on `127.0.0.1` only, unless you change
  `EPIC_API_BIND`.

## 1. Generate a token

```bash
openssl rand -hex 32
```

## 2. Put it in `.env`

```dotenv
EPIC_API_TOKEN=<paste the 64 hex characters here>
# Host address Docker publishes port 8000 on (default 127.0.0.1)
EPIC_API_BIND=127.0.0.1
# How many crews may run at once
EPIC_API_MAX_CONCURRENT=1
```

Restart the API so it picks up the new values:

```bash
docker compose up -d api
```

Check it from the API host:

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/kickoff \
  -H "Authorization: Bearer $EPIC_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_request": "Poème sur la mer"}'
```

The second call returns `202` with `"Crew kickoff initiated successfully."`.

## 3. Create the n8n credential

In n8n, open **Credentials → Create credential → Header Auth** and set:

| Field | Value |
|-------|-------|
| Name  | `Authorization` |
| Value | `Bearer <token>` (the word `Bearer`, one space, then the token) |

## 4. Add an HTTP Request node

Configure the node as follows:

- **Method**: `POST`
- **URL**: the API address, for example `https://epic.example.com/kickoff`
  (see the TLS section below)
- **Authentication**: `Generic Credential Type`
- **Generic Auth Type**: `Header Auth`, then pick the credential from step 3
- **Send Body**: on, **Body Content Type**: `JSON`
- **Specify Body**: `Using JSON`:

```json
{
  "user_request": "{{ $json.request }}"
}
```

The node gets `202` back immediately; the crew runs in the background and
writes its report under `output/`. Handle `429` with the node's
**Retry On Fail** setting or a Wait node.

## 5. Choose how n8n reaches the API

- **n8n runs in Docker on the same host**: attach n8n to the API's Docker
  network (`docker network ls` shows its exact name; Compose may prefix it with
  the project name) and call `http://epic-news-api:8000/kickoff`.
  Container-to-container traffic does not use the published port, so keep
  `EPIC_API_BIND=127.0.0.1`.
- **n8n runs elsewhere**: put a TLS reverse proxy in front of the API (next
  section) and point n8n at its `https://` URL.

## Use TLS when the token leaves the host

!!! warning "Plain http exposes the token"
    Over plain `http://` the `Authorization` header travels in clear text.
    Anyone who can see the traffic (same Wi-Fi, a router, the hosting provider)
    can read the token and start crews with it. Do not publish port 8000 on a
    public interface (`EPIC_API_BIND=0.0.0.0`) without TLS in front of it.

[Caddy](https://caddyserver.com) obtains and renews HTTPS certificates
automatically. With a DNS name pointing at the host and ports 80 and 443 open,
this minimal `Caddyfile` is enough:

```caddyfile
epic.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Caddy runs on the same host and forwards to the loopback port, so
`EPIC_API_BIND` stays at `127.0.0.1` and only Caddy is reachable from outside.
n8n then calls `https://epic.example.com/kickoff`.

If the proxy runs on another machine, set `EPIC_API_BIND` to the API host's
private address (not `0.0.0.0`) and restrict port 8000 to the proxy with a
firewall.

## Rotate the token

1. Generate a new token and replace `EPIC_API_TOKEN` in `.env`.
2. Restart the API: `docker compose up -d api`.
3. Update the n8n Header Auth credential value.
