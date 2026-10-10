# Optional personal profile

Keep the upstream agents, strategy, integrations, and scripts intact.

Only when the user explicitly selects `personal-no-extra-cost` (or its alias
`personal-free`), read
`strategy/profiles/personal-no-extra-cost/POLICY.md` before doing any task or
delegating. Apply it to every child and handoff. If these files are missing or
invalid, stop; never fall back to an unrestricted agent.

For that profile, use only existing subscription access, never LLM API keys,
credit purchases, paid fallbacks, or unverified services. Subscription limits
require checkpointing and stopping, not buying more usage. Account billing and
network controls must also be verified; this repository cannot enforce them.

The profile's Python utilities only build, validate, and copy local files.
They do not start Codex, authenticate, connect accounts, or enforce a universal
runtime firewall. Do not claim that a successful build proves cloud support,
available quota, or zero billing. See `README.ja.md` for the mobile workflow.

Without explicit profile selection, use the upstream definitions normally.
