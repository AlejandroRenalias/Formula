# Formula Development Orchestrator (O0–O5)

This is isolated development tooling around Formula. It is not part of the Formula F1 strategy application.

O0–O4 provide isolated configuration, deterministic repository preflight, workspace-scoped Codex execution, local test and GPT review gates, bounded repair control, run records, and safety invariants. O5 is the only general task front door and delegates execution to O4 after explicit human approval. The official OpenAI Agents SDK and its experimental workspace-scoped Codex tool remain behind the execution boundary.

## Check

From the Formula repository root:

```powershell
uv run --project tools/orchestrator formula-orchestrator check
```

The default repository root is discovered dynamically. Set `FORMULA_REPOSITORY_ROOT` to check another Formula checkout. A dirty tree, missing expected directories, missing repository, or non-Git directory causes a non-zero exit.

O4 repair fixture smoke:

```powershell
uv run --project tools/orchestrator formula-orchestrator repair-smoke
```

## O5 human-gated task workflow

Create a strict JSON task request containing `schema_version`, `task_id`, `title`, `objective`, `acceptance_criteria`, and a repository-relative `allowed_paths` or `allowed_roots` scope. Then prepare and inspect the plan:

```powershell
uv run --project tools/orchestrator formula-orchestrator task-prepare --task-file .\task.json
```

Preparation is local and deterministic: it performs preflight and a baseline test, but never calls Codex or GPT. Copy the printed approval token only after reviewing the exact scope, baseline, models, test policy, and repair budget. Execute once with:

```powershell
uv run --project tools/orchestrator formula-orchestrator task-run --plan-file .\tools\orchestrator\.run-logs\prepared\<task>-<fingerprint-prefix>.json --approve <token>
```

The token binds the exact fingerprinted plan; it is not an API secret. `task-run` revalidates the clean repository, HEAD, branch, policy, and a fresh baseline test before requiring environment-only OpenAI credentials and consuming the single-use execution marker. Only one task may run at a time. Execution approval is separate from finalization approval: the autonomous Codex/test/GPT loop never commits or pushes, while `task-finalize --run-file ... --approve ...` may deterministically stage only the approved paths, commit, and push `origin` after the human inspects the result. No force push, merge, or deployment is performed. Technical success is reported as `READY_FOR_HUMAN_REVIEW`; finalization success is reported as `FINALIZED`.

## Safety contract

- Future Codex execution is workspace-scoped to Formula only.
- Automatic repair loops are bounded at two by default; infinite loops are prohibited.
- The autonomous Codex/test/GPT loop performs no commit or push; deterministic Git finalization requires a separate human approval.
- Human approval is required after a future orchestrated run.
- Test and tool/model failures cannot be represented as success.
- Run records contain operational metadata only and never credential values.

Credentials must be supplied through the environment variables expected by official OpenAI tooling, such as `OPENAI_API_KEY`. Never commit `.env` files or API keys.
