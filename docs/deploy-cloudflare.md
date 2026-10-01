# Plan: put the Chess Coach dashboard online at chess.auraodonto.com.br

## Context
The FastAPI dashboard (`coach web`) runs in Docker on the Mac and reads `data/coach.db` (145 MB SQLite).
It also writes puzzle attempts and runs Stockfish for puzzle explanations, so it can't be moved to
Cloudflare Pages or Workers. The goal is to reach it from anywhere while analysis keeps running locally.

**Approach:** run a Cloudflare Tunnel (`cloudflared` container) next to the `web` container and put
**Cloudflare Access** (a login gate) in front of it, because the app has no auth of its own. Both are
free. The tunnel makes outbound connections only: no router ports opened, no home IP exposed.

**Subdomain and the existing worker:** yes, this works side by side. `auraodonto.com.br` stays served
by the existing Worker. `chess.auraodonto.com.br` gets its own proxied DNS record (a CNAME to the
tunnel). There's one thing to check (Phase 0, step 2): the Worker must not be attached through a
wildcard route such as `*.auraodonto.com.br/*`, because that route would also capture the `chess`
subdomain. The free Universal SSL certificate already covers `*.auraodonto.com.br`, so
`chess.auraodonto.com.br` gets HTTPS automatically.

```
browser → chess.auraodonto.com.br (Cloudflare edge + Access login)
        → tunnel → cloudflared container → web:8000 (compose network) → coach.db / Stockfish
browser → auraodonto.com.br → existing Worker (unchanged)
```

---

## Phase 0: Cloudflare checks (you, in the dashboard, ~5 min)
1. **Zone is fully on Cloudflare.** dash.cloudflare.com → `auraodonto.com.br` → Overview should show
   **Active**, with the nameservers at Registro.br set to Cloudflare's. A tunnel's public hostname
   needs this full setup.
2. **Worker routing.** Workers & Pages → your worker → Settings → **Domains & Routes**:
   - A *Custom Domain* `auraodonto.com.br` (and/or `www`) is fine as it is.
   - A *Route* like `*auraodonto.com.br/*` or `*.auraodonto.com.br/*` would catch `chess.` too.
     Replace it with explicit routes `auraodonto.com.br/*` and `www.auraodonto.com.br/*`.
3. **DNS.** DNS → Records: make sure there's no existing `chess` record. A wildcard `*` record
   is harmless, because the specific record created later takes precedence.

## Phase 1: Code changes (me, one commit on main)
All of this is config and docs, with no Python behaviour change, so there's no TDD cycle here.
- **`docker-compose.yml`**
  - `web`: add `restart: unless-stopped`, and bind the port to localhost only:
    `"127.0.0.1:8000:8000"`. Today it's `"8000:8000"`, which is reachable from anyone on the LAN.
  - New `tunnel` service:
    ```yaml
    tunnel:
      image: cloudflare/cloudflared:<pinned version>
      command: ["tunnel", "--no-autoupdate", "run"]
      restart: unless-stopped
      env_file:
        - path: .env
          required: false
      depends_on: [web]
    ```
    `cloudflared` reads `TUNNEL_TOKEN` from the environment. Don't use `${TUNNEL_TOKEN:?}`
    interpolation: compose would then fail on every command, including `make check`, when the token
    is unset.
- **`.env.example`**: add a commented `TUNNEL_TOKEN=` line with a short note saying it comes from
  the Zero Trust tunnel page.
- **`Makefile`**: `online` (`docker compose up -d web tunnel`) and `offline`
  (`docker compose stop tunnel`), next to the existing `schedule`/`unschedule` targets.
- **`PLAN.md`**: a short "Deployment (Cloudflare Tunnel + Access)" subsection under Containerization.
- **`CLAUDE.md`**: mention `make online` and the public URL in "Running things".
- **`TODO.md`**: add a "Online dashboard" item and tick it in the commit.
- Then `make check`, commit with the attribution trailer, and push after you confirm.

## Phase 2: Zero Trust account and login method (you, ~5 min)
1. Go to one.dash.cloudflare.com (Zero Trust) and pick a **team name** (e.g. `rlimaa` →
   `rlimaa.cloudflareaccess.com`). Choose the **Free** plan (up to 50 users). Cloudflare may ask for
   a payment method even though the plan costs $0.
2. Settings → Authentication → Login methods: **One-time PIN** (a code sent by email) is
   enabled by default. Optionally add **Google** for one-click login.

## Phase 3: Access application, created *before* the hostname goes live (you, ~5 min)
Creating the Access application first means the site is never public without the login gate.
1. Zero Trust → Access → Applications → **Add an application** → **Self-hosted**.
2. Name `Chess Coach`. Session duration: **1 month**, so you aren't asked to log in again constantly.
3. Public hostname: subdomain `chess`, domain `auraodonto.com.br`, path empty.
4. Policy: name `Only me`, Action **Allow**, Include → **Emails** →
   `rodrigolaraujo7@gmail.com` (add others if you want to share the site).
5. Login methods: One-time PIN (plus Google if enabled). Save.

## Phase 4: Tunnel and public hostname (you, then me, ~10 min)
1. Zero Trust → Networks → **Tunnels** → Create a tunnel → **Cloudflared** → name `chess-coach`.
2. On "Install connector" choose **Docker**. Copy only the token, the long string after `--token`.
   Don't run the command shown there.
3. Put it in the project's `.env` (gitignored) as `TUNNEL_TOKEN=<token>`. It's a secret: keep it out
   of the chat and out of git.
4. Next → **Public hostname** (newer UI: "Published application routes"): subdomain `chess`,
   domain `auraodonto.com.br`, path empty, Service **HTTP**, URL **`web:8000`**. This is the
   compose service name; `localhost` would be wrong from inside the container. Save. Cloudflare
   then creates the proxied DNS record `chess` → `<tunnel-id>.cfargotunnel.com` automatically.
5. SSL/TLS → Edge Certificates: turn **Always Use HTTPS** on (it may already be on for the zone).
6. Me: `make online`, then the checks in Verification below.

## Phase 5: Keep it up (you, ~2 min)
The scheduler already depends on these too:
- Docker Desktop → Settings → General → **Start Docker Desktop when you sign in**.
- macOS System Settings → Energy/Battery → **Prevent automatic sleeping when the display is off**
  (on a laptop, this only applies while it's on the power adapter).

The site is down whenever the Mac sleeps or is off. Access still shows its login page, then a
Cloudflare 1033/502 error.

## Phase 6 (optional, later): defence in depth, with TDD
- Validate Cloudflare's `Cf-Access-Jwt-Assertion` header in a FastAPI middleware, using the team
  domain and the application's AUD tag from settings. Requests that bypass Access are then rejected
  even if the tunnel is ever misconfigured. It would be tested through `create_app` with
  `TestClient`.
- Disable FastAPI's `/docs` and `/openapi.json` (`FastAPI(docs_url=None, ...)`) in
  `src/chesscoach/interfaces/web/app.py`.

---

## Verification
1. `make check` passes, and `docker compose config` is valid with and without `TUNNEL_TOKEN` set.
2. `docker compose ps`: `web`, `tunnel` and `scheduler` are all running.
   `docker compose logs tunnel` shows "Registered tunnel connection" (usually 4 connections).
3. Zero Trust → Tunnels shows `chess-coach` as **HEALTHY**.
4. `curl -sI https://chess.auraodonto.com.br` returns a 302 redirect to
   `<team>.cloudflareaccess.com`. Nothing is served without login.
5. In a private browser window: log in with the email code, the dashboard loads, and you can answer
   a puzzle and open its explanation (this exercises the POST endpoint and Stockfish).
6. `https://auraodonto.com.br` still serves the existing Worker page.
7. From another device on the LAN, `http://<mac-ip>:8000` is refused (localhost-only bind);
   `http://localhost:8000` still works on the Mac.
