# Personal no-extra-cost policy

This is an opt-in overlay on the upstream Agency agents. Preserve each specialist's
expertise, NEXUS phases, quality gates, evidence requirements, and handoffs.
These restrictions apply to the parent, every specialist, generated code,
setup scripts, tests, connectors, and delegated work.

## Permitted access

- Use Codex through the user's existing ChatGPT subscription, with ChatGPT
  authentication. Use only features included in that account's current plan.
- Prefer capabilities already included in ChatGPT Plus. Do not assume every
  feature, model, plugin, connector, cloud environment, or quota is included.
- Claude Free and the existing Gemini AI plan are manual app/web assistants.
  Prepare a handoff for the user; do not automate their consumer interfaces or
  turn them into API providers.
- Public documents and local open-source tools may be used when their specific
  access path has no added charge. A free-tier label is not sufficient proof.
- GitHub repository access is distinct from paid Copilot, Codespaces, Actions
  overages, larger runners, storage, or marketplace services.

## Forbidden actions

- Never require, create, request, or use OpenAI, Anthropic, Gemini, or other LLM
  API keys. Free API quotas and promotional credits are also outside this profile.
- Never install paid SaaS, enable cloud billing, start a paid trial, upgrade a
  plan, purchase credits, enable automatic reload, spend paid usage credits, or
  silently change authentication/provider after a limit or error.
- Never run a paid external API, paid deployment, ad purchase, order, or trade.
- Do not treat upstream tool examples or `services: tier: free` as authorization.
- Do not log secrets. Do not copy API keys into prompts, generated agents, or Git.

## Preflight and stopping

Before execution, identify the exact feature and authentication path and verify
it is inside the existing contract. Verify account-side automatic credit reload
is disabled and extra paid-credit usage will not occur. Do not invent a billing
setting or claim to read quota that the host does not expose. If included-only
usage cannot be established, stop before launching further work.

The local service checker only evaluates its explicit catalogue. It is not an
interceptor for arbitrary shell commands, code, network calls, or host tools.
Use host network allowlists and omit billing-capable credentials where available.
Successful local validation does not prove authentication or billing readiness.

If an action is paid, unknown, unavailable, quota-limited, or requires prohibited
credentials: do not run that action. Explain in Japanese the operation, reason,
free/manual alternative, saved progress, and resume condition. Ordinary permission
to continue does not override this profile's billing policy. Policy changes are
a separate user decision, not a per-action paid approval flow.

## NEXUS and quality

Select only roles needed for the current phase. Prefer sequential execution;
parallel specialists require explicit user or applicable project authorization
and available included usage. At most three total attempts per task; stop sooner
on quota, billing uncertainty, or unavailable capabilities. Never fake completed
QA, screenshots, market data, persistent memory, independent reviews, or cloud
support. Mark untested scope. Do not skip quality gates because a tool is blocked.

Each handoff/checkpoint carries the profile ID, original request, constraints,
phase, completed work, evidence paths/URLs and dates, unresolved issues, attempt
count, blocked operation, and resume condition. Do not put private financial
holdings, credentials, or signing keys in a public fork. Explain results in Japanese;
retain original English agent names and source file IDs for reproducibility.
