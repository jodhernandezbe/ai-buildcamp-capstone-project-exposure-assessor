# prompts/ rules

Project-wide guidance is in the root `CLAUDE.md`; these rules apply to work in `prompts/`.

- Prompts live in `prompts/*.md`. Never inline prompt text in Python.
- Load prompts through `prompts.registry.load_prompt`.
- Structure prompts with XML tags (`<role>`, `<context>`, `<instructions>`,
  `<output_format>`).
