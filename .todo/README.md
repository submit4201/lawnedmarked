# .todo Directory

This directory tracks TODO items, FIXMEs, and other code annotations.

## Structure

```
.todo/
├── .done/              # Completed items (compressed archives)
├── parsed-YYYY-MM-DD.md  # Parsed TODO items by date
└── README.md           # This file
```

## Purpose

Per User Rule 4-E through 4-J, comments with markers like:
- `[ ]` - Uncompleted tasks
- `[x]` - Completed tasks
- `TODO:` - Tasks to do
- `FIXME:` - Bugs to fix
- `HACK:` - Temporary solutions
- `?` - Questions
- `!` - Important items
- `*` - Notes

Should be parsed periodically and logged here for review.

## Comment Markers

| Marker | Purpose | Example |
|--------|---------|---------|
| `# !` | Important | `# ! Critical security check` |
| `# ?` | Question | `# ? Should this be async?` |
| `# *` | Note | `# * See RFC 2324 for details` |
| `# TODO:` | Task | `# TODO: Add validation` |
| `# FIXME:` | Bug | `# FIXME: Race condition here` |
| `# HACK:` | Workaround | `# HACK: Temp fix for #123` |

## Workflow

1. **Parsing**: A scheduled task scans codebase for markers
2. **Logging**: Found items are written to `parsed-{date}.md`
3. **Review**: Team reviews items during standups
4. **Completion**: Resolved items move to `.done/`
5. **Archival**: Old completed items are zipped weekly

## Future Implementation

A comment parser script should:
1. Scan `backend/` and `frontend/src/` directories
2. Extract lines matching marker patterns
3. Generate markdown report with file links
4. Run on pre-commit or via cron

## Notes

- Review items weekly
- Prioritize FIXME over TODO
- Don't let this directory grow unbounded
