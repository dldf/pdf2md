# Working constraints

- Keep tasks narrowly scoped and minimize usage.
- Do only the specific change requested. Do not expand it into cleanup,
  modernization, documentation, tooling, or unrelated fixes.
- Inspect only files needed for the change. Avoid broad repository exploration,
  repeated checks, and exhaustive validation.
- Explain the intended change before editing. Preserve unrelated user changes.
- For folder moves, update affected references without rewriting moved content.
- Use the smallest relevant verification. Run the entire test suite only when
  the change requires it.
- If substantial additional work is discovered, describe it briefly and stop
  before doing it.
- Finish with a short summary of what changed and what was verified.
