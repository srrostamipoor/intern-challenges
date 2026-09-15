# Challenge 8 - Merge vs Rebase

## What I did
I created a scenario with a guaranteed merge conflict: I branched off `main`,
changed the same line of a file on both `main` and the `feature` branch, and
committed both. First I merged the feature branch into main and resolved the
conflict. Then I reset back and did it again, this time rebasing the feature
branch onto main and resolving the conflict during the rebase. Below is the
commit-history difference between the two approaches, plus when I'd prefer each.

## Setup (creating the conflict)
1. Created `file.txt` with one line on `main`.
2. Branched off with `git checkout -b feature` and changed line 1 to
   "changed by FEATURE", committed.
3. Switched back to `main` and changed the same line to "changed by MAIN",
   committed.

Now both branches changed the same line differently - a guaranteed conflict.

## Scenario 1: merge
- Ran `git merge feature` on `main`.
- Git reported `CONFLICT (content): Merge conflict in file.txt`.
- The file contained both versions between `<<<<<<<`, `=======`, `>>>>>>>`
  markers. I edited it to a resolved line, removed the markers, then
  `git add file.txt` and `git commit`.

History after merge (`git log --graph --oneline`):
```
*   Merge feature into main, resolve conflict
|\
| * Change line 1 on feature branch
* | Change line 1 on main branch
|/
* Initial commit: add file.txt
```
A branch-shaped history with a merge commit - you can see the branch split off
and come back together.

## Scenario 2: rebase
- Reset main back to before the merge with `git reset --hard <commit>`.
- Switched to `feature` and ran `git rebase main`.
- Got the same conflict. I resolved the file, `git add file.txt`, then
  `git rebase --continue`.

History after rebase (`git log --graph --oneline`):
```
* Change line 1 on feature branch
* Change line 1 on main branch
* Initial commit: add file.txt
```
A clean, linear history - no merge commit, no branching. The feature commit
now sits directly on top of main, as if it was written after it.

## The difference

| | Merge | Rebase |
|---|---|---|
| History shape | Branched (`|\ ... |/`) | Linear / straight |
| Extra merge commit? | Yes | No |
| Real parallel history | Preserved | Flattened (hidden) |

## When I'd prefer each on a team
- **Merge**: for shared branches. It preserves the true history and is safer
  when several people are working on the same branch, because it doesn't
  rewrite existing commits.
- **Rebase**: to tidy up my own local branch before sharing it, since it gives
  a clean linear history. But I would **not** rebase a branch that others are
  already using, because it rewrites history and can break their work.

**In short:** merge for shared work and honest history; rebase to clean up a
private branch before merging it in.

## Note
Practiced in a separate repo (`merge-rebase-practice`) to keep the history
isolated. This README documents both scenarios and the resulting graphs.
