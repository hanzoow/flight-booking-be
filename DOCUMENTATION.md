# Flight BFF — supplementary notes

The **primary assessment write-up** (API design, architecture, resilience, caching, AI workflow, and local setup) is in **[README.md](README.md)** under **Documentation (take-home deliverable)**. Keep that section accurate for submission.

**Cursor:** Project **Rules** live in `.cursor/rules/*.mdc`; the **Skill** `flight-bff-extend-api` lives under `.cursor/skills/`. See README → **Cursor: Rules & Skills**.

This file only holds **optional extras** you can expand if the brief asks for more depth without bloating the README.

## Implementation checklist (incremental)

1. Scaffold & config — `requirements.txt`, `app/config.py`, `app/main.py`, `/health`.
2. Legacy client — async `httpx`, retries, circuit breaker, forward `simulate_issues`.
3. Errors — `AppError`, handlers, `normalize_upstream_error_payload` for four legacy shapes.
4. Airports — list + city enrichment (parallel per-code fetches), TTL cache.
5. Search — flatten legs, labels, normalized pricing, BFF pagination.
6. Offer / booking — transform + validation; booking GET cache.
7. Verify OpenAPI at `/docs`; deploy (e.g. Render) using `render.yaml` / README.

## Diagram source

The mermaid diagram in README is the canonical architecture figure; export to PNG/PDF from GitHub or a Mermaid renderer if the grader wants an image file.
