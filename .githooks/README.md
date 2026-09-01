# .githooks

Versioned git hooks for this repo. One hook lives here: `pre-push`, the
publish gate for `main`.

## Install (once per clone)

    ./.githooks/install

That sets `core.hooksPath` to this directory. Until it is run, the hook is
present in the working tree but **does not run**.

## What the gate does

`main` is what GitHub Pages builds the public site from, so a push to `main`
is a publication. `publish_content` is autonomy level 1 and locked: no agent
may approve it, only zsotte. The hook therefore blocks a push to `main`
unless a fresh approval token exists:

    /home/zsotte/marveen/store/zsotte-com-push-approval

The token is valid for one hour and is consumed by one push (moved aside to
`.inflight`, so a failed push can restore it with a single `mv`). Pushes to
any other branch are not gated -- they publish nothing.

## What this does NOT protect against

- **A clone where `install` was never run.** The script travels, the config
  does not.
- **`git push --no-verify`.** Any client-side hook can be skipped on purpose.
- **A push from another machine, another checkout, or the GitHub web UI.**

All three have the same fix, and it is server-side: a branch protection rule
or ruleset on `zsotte/zsotte.github.io` that requires a pull request for
`main`. That changes repository settings, which is zsotte's decision, not an
agent's. Kanban card `0a44e6ef` tracks it.

A client-side hook is a reminder at the right moment, not a lock. Read it as
one.
