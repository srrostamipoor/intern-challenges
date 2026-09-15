# Challenge 9 - Collaboration Workflow

## What I did
I forked a public repo, made a small meaningful change, opened a pull request
back to the original project, left a review comment on my own PR, and then
addressed that feedback with a follow-up commit (not a force-push).

## Steps
1. **Forked** the public `first-contributions` repo into my own account, so I had
   my own copy to work on (I don't have direct access to the original).
2. **Cloned** my fork to my machine with `git clone`.
3. Created a branch `add-my-name` and added my name to `Contributors.md`, then
   committed and pushed it to my fork.
4. Opened a **pull request** from my fork's branch to the original repo's `main`.
5. Left a **review comment** on the PR: my name should include my GitHub profile
   link to match the format of the other entries.
6. Addressed the feedback with a **follow-up commit** - I edited the line to
   `[Sara Rostamipoor](https://github.com/srrostamipoor)` and pushed it. The PR
   updated automatically to show the second commit, without rewriting history.

## Why follow-up commits, not force-push
The task specifically asked to address feedback with follow-up commits rather
than force-pushing over the history. A follow-up commit keeps the history honest:
you can see the original commit, the review comment, and then a second commit
that fixed it. Force-pushing would rewrite history and hide that the review ever
happened, which is bad on a shared PR that others are reviewing.

## Key concepts I learned
- **Fork vs branch:** a fork is a full copy of someone else's repo in my own
  account; a branch is a parallel line of work inside one repo. Fork is for
  contributing to projects I don't own.
- A PR follows a **branch**, so any new commit I push to that branch appears in
  the PR automatically - no need to open a new PR.
- Changes in a PR are only a **proposal**; they don't enter the original repo
  until the project owner merges the PR.

## Deliverable
- **Pull request:** https://github.com/firstcontributions/first-contributions/pull/124971
- The PR shows the review comment and the follow-up commit addressing it.
- **My fork:** https://github.com/srrostamipoor/first-contributions
