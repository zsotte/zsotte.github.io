# .githooks

Versioned git hooks for this repo. One hook lives here: `pre-push`.

## Install (once per clone)

    ./.githooks/install

That sets `core.hooksPath` to this directory. Until it is run, the hook is
present in the working tree but **does not run**.

## What publishing looks like

`main` is what GitHub Pages builds the public site from, so landing a commit on
`main` is a publication, and publication is the owner's decision alone.

Since 2026-09-01 a repository ruleset on `main` requires a pull request, with no
bypass actors. A direct push to `main` is refused by GitHub itself. So the route
is:

    branch -> push the branch (free, publishes nothing) -> pull request
           -> the owner approves -> MERGE, and the merge is the publication

## What the hook is for

Not for holding that line -- the ruleset holds it, on the server, where
`--no-verify` and a second clone cannot reach around it.

The hook does the thing a server-side refusal does badly: when someone pushes to
`main` out of habit, it stops early and prints the route above, instead of
letting them read `GH013` and guess. Pushes to any other branch pass straight
through.

Read it as a signpost, not a lock. A client-side hook can always be skipped on
purpose, and skipping this one costs nothing, because what it explains is
enforced elsewhere.
