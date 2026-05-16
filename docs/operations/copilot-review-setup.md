# Playbook: Enable Copilot code review for all PRs

Use this once per repository to ensure GitHub Copilot automatically reviews every pull request.

## Prerequisites

- You have **Admin** (or equivalent settings) access to the repository.
- GitHub Copilot is enabled for your user/org.

## Enable automatic Copilot review

1. Open your repository on GitHub.
2. Go to **Settings**.
3. In the left sidebar, open **Code review**.
4. Open the **Copilot** section.
5. Turn on **Enable for all pull requests**.
6. Save/apply the setting if prompted.

## Review comment conventions

When Copilot leaves review comments:

1. **Address**  
   - Make the code/doc change, then reply to the comment with what was changed.
2. **Resolve**  
   - After the fix is pushed (or explanation is accepted), use **Resolve conversation** on the thread.
3. **Dismiss (when not applicable)**  
   - If feedback is not applicable, reply with rationale and dismiss/close the thread per your repo policy.

## Merge and approval note

Copilot cannot self-approve its own pull requests. If policy allows and merge is still required, a repository admin can merge with:

```bash
gh pr merge <PR_NUMBER> --admin
```
