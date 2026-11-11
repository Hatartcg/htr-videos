---
name: model-router
description: Pick the cheapest Claude model that can do each piece of work well, to keep credit use low. Use when planning multi-step work, delegating subtasks, creating or reviewing scheduled tasks, or when Hadi asks to save credits.
---

# Model router — cheapest model that does the job well

Goal (owner, 11 Nov 2026): spend the minimum credits. A stronger model only where it changes the result.

## What can and cannot be switched (be honest about this)
- **This conversation's own model cannot be switched by Claude.** Only the person can change it in the app's model picker. When the current work is simple enough for a cheaper model, or hard enough to need a stronger one, say so in ONE short Arabic line (e.g. «الشغل الجاي بسيط — تقدر تحوّل لـ Sonnet وتوفّر») and carry on. Never pretend to have switched.
- **Subtasks inside a session** can run on a cheaper model: the Agent tool takes `model` = `haiku` | `sonnet` | `opus`.
- **Scheduled tasks** each have their own model (`update_trigger` → `model`). Changing a task's model is done only after the owner says «نفّذ» to the proposed change.

## Tiers
| Tier | Model | Use for |
|---|---|---|
| 1 — cheap | haiku | Reading/summarising pages or files, status checks, monitors that usually end silently, extracting numbers from a page, renaming/moving files, simple formatting, checking a deploy status, lookups |
| 2 — normal | sonnet | Routine code edits, blog posts and captions, daily reports, browser form-filling (Rewaa, Salla), data cleanup, research with a few searches |
| 3 — strong | opus | Security review, architecture/new apps, hard debugging, money or irreversible decisions, negotiations and business emails, anything where a mistake costs the owner money or trust, voiceover scripts with his strict pronunciation rules |

Rule of thumb: start at the lowest tier that can plausibly do it; move up only if the task is risky, ambiguous or failed once at the lower tier. Never move down for work touching payments, security, customer messages or anything irreversible.

## Inside a session: when delegating pays off
A subagent starts cold and re-reads context, so delegate only **big, self-contained, low-judgement chunks** (e.g. "read these 20 product pages and return name/price/stock as JSON", "scan this folder and list files over 50 MB"). Give it a complete brief and ask for a short, structured result. Do small steps yourself — spawning for a one-minute task costs more than it saves. Only spawn agents when the owner's instructions or this skill's routing clearly calls for it.

## Scheduled tasks
When creating a scheduled task, choose its tier from the table and include the recommendation in the summary shown to the owner. When reviewing existing ones, list each task → current model → suggested model → why, and apply only after «نفّذ». Typical: silent hourly monitors and status reports → haiku; content/report writers → sonnet; security guards, builders and anything that sends or spends → opus.

## Reporting
Reply to Hadi in Saudi Arabic. When a cheaper model was used for part of the work, mention it in one line only if it matters (e.g. a result to double-check).
