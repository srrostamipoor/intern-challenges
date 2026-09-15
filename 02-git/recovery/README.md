# Challenge 10 - Recovery Tools

## What I did
I deliberately broke things three different ways and recovered each one using
the right Git tool, and documented why that specific tool was the correct choice
for each situation.

## Scenario 1: recovering a "lost" commit with git reflog
**What broke:** I made a commit ("Add important work"), then ran
`git reset --hard HEAD~1`, which removed it from the history. `git log` showed
it was gone.

**Recovery commands:**
```
git reflog                 # shows every action, including the "lost" commit
git reset --hard 347c493   # jump back to the lost commit's hash
```

**Why reflog was the right choice:** `git log` only shows the current history,
so the commit looked gone. But Git doesn't immediately delete anything - `reflog`
is a record of every position HEAD has been in, so the "lost" commit was still
there. reflog is the right tool when you accidentally reset or delete a local
commit and need to find its hash to get it back.

## Scenario 2: undoing a pushed bad commit with git revert
**What broke:** I made a bad commit and **pushed it** to GitHub, so it was now
shared history that others could have.

**Recovery command:**
```
git revert 372ced9   # creates a NEW commit that undoes the bad one
git push
```

**Why revert, not reset:** The bad commit was already pushed and shared. If I
used `reset` to delete it, I'd rewrite shared history - my history would no
longer match everyone else's, which breaks their repos and causes conflicts.
`revert` instead adds a new commit that reverses the bad change, leaving the
original commit in place. The history stays honest (you can see the bad commit
and the commit that fixed it) and nothing shared is rewritten. So: reset is fine
for local-only commits, but revert is the safe choice for anything already
pushed.

## Scenario 3: setting work aside with git stash
**What broke (well, blocked me):** I had uncommitted changes ("work in progress")
but needed to switch branches to do something else. Git won't cleanly let you
switch with uncommitted work in the way.

**Commands:**
```
git stash                  # set the uncommitted changes aside
git checkout -b other-task # switch and do unrelated work
git commit ...             # (work on the other task)
git checkout main          # come back
git stash pop              # bring the set-aside changes back
```

**Why stash was the right choice:** I wasn't ready to commit the work-in-progress
(committing half-done work would clutter the history), but I still needed a clean
working directory to switch branches. `stash` saves the changes temporarily
without committing them, so I can switch away, do other work, and then `stash pop`
to continue exactly where I left off. It's the right tool when you need to pause
messy, unfinished work without committing it.

## Summary
| Situation | Tool | Why |
|---|---|---|
| Lost a local commit | `git reflog` | finds commits that `git log` no longer shows |
| Bad commit already pushed | `git revert` | undoes it without rewriting shared history |
| Unfinished work, need to switch | `git stash` | pauses changes without committing them |

## Practice repo
https://github.com/srrostamipoor/recovery-practice
