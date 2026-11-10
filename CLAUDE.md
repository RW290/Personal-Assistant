# Personal Assistant: how to work with me

The plan (what this is, the core, status, milestones, stack, trust rules, privacy, design) lives in README.md, the only place it's written down. It's pulled in here:

@README.md

This file holds only how I want you to work.

## How to work with me
- Explain changes in plain, simple terms. Say what a piece of code does and why, not just what you changed.
- I write the core agent loop myself (the tool-calling loop, approval queue and action log). For those files, guide me and review my code instead of writing them wholesale, unless I ask you to.
- When I'm debugging, give me a hint first, not the full fix.
- Python 3. Simplest solution first, with plain lists and dicts. Keep dependencies small. No agent frameworks (LangChain etc.) until after Milestone 4; the router, later, is where LangGraph comes in.
- Small, working steps. After each milestone, help me write a 4-line write-up: the problem, what I tried, numbers before and after, what's next.
- Build the core first. Don't build toward anything in README's "Later, not core" until the core is done.
- The trust rules and privacy rules in README.md are hard rules: never break them, in code or in suggestions.
- Never put API keys in code. They live in `.env` locally (listed in `.gitignore`) and in Replit Secrets when deployed. Never commit `.env`.

## Keeping things current
- Whenever we change the plan (a decision, a model or tool choice, a milestone, the scope), write it into README.md in the same change. Change this file only when how I want you to work changes.
- Keep README's Status section current: update it in the same change whenever something is finished, merged, or the next step changes.
- Keep the GitHub repo description and topics in sync with the plan too. Both describe the finished assistant, not what works today. The description is mostly what it does, then a short list of the main tools (Claude, LangGraph, and so on), in 350 characters at most. The topics name the main tools and techniques (langgraph, rag, pwa, and so on), up to 20. Whenever a plan change affects either, update it in the same change with `gh repo edit` (`--description`, `--add-topic`, `--remove-topic`). I've okayed these updates, so no need to ask first.
- Keep `docs/privacy.md` true. It's the privacy policy Google's sign-in screen links to: whenever the plan changes which Google data it uses or where that data goes, update it in the same change.
- Commit freely, but always on a new branch with a pull request into `main`, so I can review it on GitHub. Never push to `main` directly; I merge. The repo is public: check every commit for secrets before pushing.
