# Archived Projects

This folder contains projects that have been archived to reduce clutter in the main projects folder.

## Why Archive?

Projects are archived when they:
- ✅ Completed their purpose
- ✅ Have low future reference value
- ✅ Are no longer referenced in active documentation
- ✅ Have lessons learned captured elsewhere

## Discovering Archived Projects

Browse this directory or use git history to explore past projects:

```bash
# List archived projects
ls -d specs/projects/_archive/*/

# View git history for a project
git log --follow -- specs/projects/_archive/<project-name>/
```

## Restoring Projects

If an archived project becomes relevant again:

```bash
# Move back to active projects
mv specs/projects/_archive/<project-name> specs/projects/<project-name>

# Update its STATUS.md to reflect reactivation
```

## See Also

- [Project Lifecycle Playbook](../../../playbooks/project-lifecycle.md) - Full lifecycle management guide
- [Active Projects](../) - Current and reference projects
- [Examples](../../../examples/) - Working implementations
