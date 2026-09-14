# Challenge 7 - Branching Strategy

## What I did
I created a repo with a `main` branch, implemented a small feature using a
proper feature-branch workflow (branch, several small atomic commits, a pull
request, then merge), then simulated a second scenario using trunk-based
development (a short-lived branch merged the same day). Below is the repo
history showing both, plus a comparison.

## Feature-branch workflow
1. Created a branch `add-greeting` off `main`.
2. Made three small atomic commits, each one logical change:
   - "Add greeting function skeleton"
   - "Implement greeting message"
   - "Add farewell function"
3. Pushed the branch and opened a **pull request** on GitHub.
4. Merged the PR into `main`.

## Trunk-based workflow
1. Created a short-lived branch `quick-fix` off `main`.
2. Made one small quick change (updated the README description).
3. Merged it directly into `main` the same day (no long-lived branch).

## Repo history (deliverable)
Output of `git log --graph --oneline --all`:
```
* 4acfd2f (HEAD -> main, quick-fix) Update README with project description
*   6772349 Merge pull request #1 from srrostamipoor/add-greeting
|\
| * 2f1464d Add farewell function
| * 4b04be6 Implement greeting message
| * af2057d Add greeting function skeleton
|/
* cec6091 Initial commit: add README
```
You can see both workflows in the graph:
- The **feature-branch** part branched off, got three small commits, and came
  back into `main` through a merge commit (the "Merge pull request #1" line and
  the `|\ ... |/` fork). This shows an isolated branch that was reviewed via a PR.
- The **trunk-based** part (the top "Update README" commit) went almost straight
  onto `main` - a small change merged the same day without a long-lived branch.

## Comparison: when I'd use each

**Feature-branch workflow**
- Best for larger or more complex features that take days to build.
- The branch stays isolated so unfinished work never destabilizes `main`, and the
  PR gives a clear place for code review before merging.
- Trade-off: if the branch lives too long, it drifts from `main` and merging can
  cause many conflicts.

**Trunk-based development**
- Best for small, quick changes where the team wants continuous integration.
- Short-lived branches merged the same day keep everyone close to `main`, so
  conflicts stay small and code ships faster.
- Trade-off: not suitable for large, half-finished work, since changes reach
  `main` quickly.

**In short:** on a real team I'd use feature branches for big, review-heavy
features, and trunk-based for small, frequent changes where fast integration
matters more than long isolation.

## Note
This was practiced in a separate repo to keep the history
clean. This README documents the workflow, commits, PR, and the resulting graph.

## Practice repo
The actual commits, branch, and pull request live here:
https://github.com/srrostamipoor/branching-practice
