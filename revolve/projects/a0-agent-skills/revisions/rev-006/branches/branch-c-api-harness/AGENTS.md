# revolve/projects/a0-agent-skills/revisions/rev-006/branches/branch-c-api-harness/AGENTS.md

## Branch ID

`branch-c-api-harness`

## Starting Checkpoint

`cp-b001-deeper-architecture`

## Hypothesis

Branch-a and branch-b proved architecture via framework runtime tests. Branch-c expands the harness to Layer 4: deterministic HTTP/API tests that verify plugin behavior through the running web server without requiring live LLM turns. This includes testing plugin management endpoints, skills catalog API, and command resolution.

## Strategy

1. Investigate available HTTP API endpoints (plugin catalog, skills catalog, command resolution, project metadata, logs)
2. Build deterministic HTTP tests against running server (port 80)
3. Verify plugin skills catalog is accessible via API
4. Verify command resolution works via API
5. Document which tests belong in Layer 4 vs Layer 5

## Candidate Checkpoints

| Checkpoint | Parent | Status | Result | Detail |
|---|---|---|---|---|
| none yet | — | — | — | create candidate |

## Best Result

`cp-c001-api-harness`: 4/4 HTTP API tests passed. Plugin discoverable via `/api/plugins_list`, skills via `/api/skills`, projects via `/api/projects`, catalog via `/api/plugins/_skills/skills_catalog`.

## Status

`promoted` externally.

## Continuation/Termination Reason

Branch objective achieved. Layer 4 HTTP/API tests prove plugin behavior through the running web server without live LLM.

## Reusable Insights

- A0 auth flow: POST to `/login` with form data, then GET `/api/csrf_token`, then use token in `X-CSRF-Token` header.
- `/api/skills` returns data as a list, not a dict.
- `/api/projects` returns data as a list, not a dict.
- `_skills` plugin exposes `/api/plugins/_skills/skills_catalog` endpoint for catalog management.
