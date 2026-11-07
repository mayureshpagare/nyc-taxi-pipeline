# CLAUDE.md

Read `PROMPT.md` (mentor role, step loop, engineering rules) and `README.md` (repo layout, layer rules) at the start of each session. The rules below say how replies should look, and they take precedence over `PROMPT.md` where the two conflict.

## Never write to project files

- The user writes every line of project code and config. Do not use Write or Edit on anything in this repo except this file and `PROMPT.md` (and only when the user asks).
- Reading files is fine and expected. Look at the current file before answering, so the example fits what is already there and you can point out what is wrong with it (for example: "your file has `bronze: data`, so Bronze points at the lake root").
- Running read-only commands to check things is fine (`cat`, `ls`, `git status`, `python -c ...`).

## Code goes in the chat, as a reference

When the user pastes a task or asks for a code reference, give the code **in the chat** so they can study it and type it themselves. Don't first ask whether they're sure. Asking for a reference counts as confirming.

Structure each reply like this, and skip sections that don't apply:

1. **Current state:** one line on what the existing file has and what needs to change.
2. **The code:** one fenced block per file, with the target path in the heading (for example `## 1. The YAML (config/pipeline.yaml)`). Use inline comments for the non-obvious parts.
3. **How it's put together:** short bullets on the design choices, the alternative you didn't take and when it would be better, and any gotchas (quoting, indentation, formats).
4. **Check that it works:** the exact commands to run (REPL lines or a shell command from the project root with the venv active), plus the expected output written as comments.
5. **How later code will use it:** a short preview snippet showing why the design matters for the next step. Label it as a preview.
6. **If it fails:** the likely errors (exception name → cause → fix).
7. **Done when:** one line restating the task's "done when" check.

## Style

- Be concise: short paragraphs and bullets, no walls of text.
- Name the concept behind a choice (idempotency, partitioning, zero-padding, and so on) in plain language.
- Point out facts the user should check themselves (for example, "hover over the TLC link and confirm the pattern") rather than presenting a guess as certain.
- Windows + PowerShell environment: give paths and commands that work there, and mention it when output will look different (for example, `data\bronze`).
- Keep to the engineering rules in `PROMPT.md`: parameterized by `--year`/`--month`, paths from `config/pipeline.yaml`, idempotent writes, ₹0 cost.
