# Working constraints

- Never make changes unless the user explicitly requests them or grants
  permission beforehand. Questions and requests for explanations do not
  authorize changes.
- Keep tasks narrowly scoped and minimize usage.
- Before implementing a feature, inspect relevant work on
  `archive/accessconverter-pilot` and reuse suitable parts without restoring
  unrelated infrastructure.
- Do only the specific change requested. Do not expand it into cleanup,
  modernization, documentation, tooling, or unrelated fixes.
- Inspect only files needed for the change. Avoid broad repository exploration,
  repeated checks, and exhaustive validation.
- Explain the intended change before editing. Preserve unrelated user changes.
- Before making coding changes, present an assessment table with columns:
  `#`, `Proposed change`, `Effort`, `Regression risk`, and `Main uncertainty`.
  Number the rows so the user can select which changes to implement. Use
  Low/Moderate/High ratings, and distinguish document-specific corrections
  from general converter fixes where relevant.
- Immediately below the table, add a short note with recommendations,
  caveats, dependencies, and any conflicts with existing behavior,
  instructions, or other proposed changes. State when none are identified.
- Wait for the user's row selections before implementing the assessed
  changes. Implement only the selected scope; do not request approval again
  for rows the user has already approved. If new work or materially different
  risks emerge, update the assessment before expanding the scope.
- For folder moves, update affected references without rewriting moved content.
- Use the smallest relevant verification. Run the entire test suite only when
  the change requires it.
- If substantial additional work is discovered, describe it briefly and stop
  before doing it.
- Finish with a short summary of what changed and what was verified.
