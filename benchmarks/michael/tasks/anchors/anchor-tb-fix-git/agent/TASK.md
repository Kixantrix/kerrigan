# Recover lost commit changes in a personal-site git repository and merge them into master (Terminal-Bench 2.0 fix-git)

Public anchor: Terminal-Bench 2.0 task `fix-git`, converted for the native closed file-tool path. The original instruction is reproduced verbatim, followed by the contract that replaces its shell environment.

## Original instruction

I just made some changes to my personal site and checked out master, but now I can't find those changes. Please help me find them and merge them into master.

## Native environment contract

- You cannot run shell commands, install packages or start services. You can read the listed files, write the final-state artifacts below and run your own Python self-tests.
- Paths: agent path `x/y` is `/x/y` in the task's container; `app/personal-site-gitdir/` is `/app/personal-site/.git/`.
- Final state (collected exactly; nothing else is graded):
  - `app/personal-site/_includes/about.md` -> `/app/personal-site/_includes/about.md`
  - `app/personal-site/_layouts/default.html` -> `/app/personal-site/_layouts/default.html`
- After you stop, a trusted verifier writes these artifacts into the task's own image and runs the task's original tests with no network.
- Not exported (92 files: binary, oversized or outside the workspace bound); the listed files are all you can read.
