# Formula Development Orchestrator (O0)

This is isolated development tooling around Formula. It is not part of the Formula F1 strategy application.

O0 provides configuration, deterministic repository preflight, a minimal run-record model, safety invariants, and a `check` CLI command. It deliberately does not call GPT, execute Codex, edit files, run repair loops, or perform Git automation. The intended future orchestration layer is the official OpenAI Agents SDK and its experimental workspace-scoped Codex tool; that integration belongs to a later milestone.

## Check

From the Formula repository root:

```powershell
uv run --project tools/orchestrator formula-orchestrator check
```

The default repository root is discovered dynamically. Set `FORMULA_REPOSITORY_ROOT` to check another Formula checkout. A dirty tree, missing expected directories, missing repository, or non-Git directory causes a non-zero exit.

## Safety contract

- Future Codex execution is workspace-scoped to Formula only.
- Automatic repair loops are bounded at two by default; infinite loops are prohibited.
- No automatic commit, push, merge, deployment, or file editing is performed by O0.
- Human approval is required after a future orchestrated run.
- Test and tool/model failures cannot be represented as success.
- Run records contain operational metadata only and never credential values.

Credentials must be supplied through the environment variables expected by official OpenAI tooling, such as `OPENAI_API_KEY`. Never commit `.env` files or API keys.
