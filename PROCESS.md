# Process — Homework 9: the promo page

One row per step. After each step the work is committed and a row is added here: the step, what the tool did, and what I decided.

| # | Step | What the tool did | What I decided |
|---|------|-------------------|----------------|
| 1 | Before you start: one commit and one PROCESS.md row per step | Claude read the session 8 slides (`08.pdf`), created this file, wrote the homework's requirements into `PLANNING_LOG.md` and committed both | To build the page first and the video afterwards; that after each step Claude commits and adds a row here |
| 2 | Install the tools: gstack (for `/office-hours`) and Impeccable | Claude installed Bun 1.4.4 (gstack needs it), cloned gstack into `~/.claude/skills/gstack` and ran its setup (it added a Stop hook to the global settings; the old settings are backed up), and ran `npx impeccable install --providers=claude --scope=project`, which put the skill, four agents and its design hooks into this project's `.claude/` | To install Bun and gstack globally and Impeccable for this project only; Claude left Impeccable's files and the teacher's `08.pdf` out of git |
