# deploy/ — E5.7

One image (`../Dockerfile`), one process, one host: the read-only FastAPI
serving ONE pinned run directory and the static viewer at `/`. Same-origin,
so there is no CORS to configure; read-only, so there is nothing to protect
from writes; every failure the API can have is a refusal at startup or a
designed JSON 404 — not an empty map.

## What run it serves, and how that is traceable

1. The E5.6 job uploads `run-<sha>` (the whole run directory, 30-day
   retention). Download it into `deploy/run/` — gitignored; **serving is not
   committing** (E5.1), and a run directory never enters `data/` (the
   `author_inherited_from` trigger, BACKLOG §3).
2. `docker build --build-arg GIT_SHA=<sha> -t ccz-viewer .` — the image
   carries the SHA as `org.opencontainers.image.revision`; the run inside it
   carries `run_id: ci-<sha>` and its `content_hash`.
3. Through the URL, `/runs` names the run and its hash; `/runs/{id}/manifest`
   returns the record's bytes; every file's ETag is its recorded sha256 — the
   deployed bytes are the CI-built bytes, verifiable by hash.

Local rehearsal: `docker compose up viewer` (the `viewer` service in
`../docker-compose.yml`), then `python deploy/verify_deployment.py http://localhost:8000`.

## Where (the host) — proposal; the provider is Karl's

The page is one static file plus ~450 KB of exports; the API is a small
read-only process over a 2.75 MB directory. One host for both is obviously
right — the API already serves the page, and two hosts would buy a CORS
surface and a second failure mode for nothing. Candidates, each running the
same image:

| provider | cost | uptime / notes |
|---|---|---|
| Fly.io (shared-cpu-1x, 256 MB) | ~US$2–3 / month at this size; free allowances vary | sleeps off by default; custom domain + TLS included |
| Render (web service) | free tier sleeps after idle (cold starts ~30 s — a first load that looks broken); US$7 / month to stay warm | TLS included |
| a small VM (any cloud, 1 vCPU) | ~US$4–6 / month | Karl operates uptime, TLS and updates |

Recommendation: Fly.io or Render's paid tier — the free tier's cold start
would render as a connection failure to the first visitor, which the viewer
reports honestly but which is avoidable for a few dollars. **The provider
account, billing and DNS are Karl's; nothing here needs a decision beyond
that.**

## Sentry — declined

A hosted service dependency for one static page and a small read-only API.
What failure would it catch that the API's logs (uvicorn's access log; a
startup refusal is a non-starting container) and the viewer's three
designed no-run states (API unreachable / no runs / no layers — distinct by
design, E5.3) do not? None identified. Declined; revisit only if a class of
failure appears that neither surface reports.

## What the URL claims

A shared link renders a preview card from `<title>` and `<meta>` — no
JavaScript runs there, so the verdict banner cannot survive into it. The
page's title and description therefore carry the STANDING status in plain
text (non-scientific until Checkpoints 1/3/4; the claim verdict is on the
page), and must be updated the day the facts change — the trigger is on the
CP5b entry. What a card cannot carry: the failing precondition by name, the
per-layer reasons, the hatch. Those are on the page, above the fold, on
every load.

## Verification — before any URL is shared

`python deploy/verify_deployment.py <public-url>` runs the same checks the
suite runs against the app, THROUGH the URL: the SRI pins at the served
page; the verdict with both halves; both watermark forms per layer; the
hatch's two labels; the stations' origin apart from the run's; the mask
distinct from the hatch; the context registry with its citations; a content
hash spot-checked through the URL against the manifest; the designed 404s as
JSON (an nginx/502 page is not one of them); POST refused. Then the
fresh-run look through the public URL, by eye, reported.
