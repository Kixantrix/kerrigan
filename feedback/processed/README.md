# Processed Feedback

Short-lived staging area for feedback that has been reviewed but not yet acted on.

## Usage

A feedback file lands here only while it is mid-resolution. Once its lesson is
absorbed — into `AGENTS.md`, repo memory, a code/validator change, or a
dispatched issue — **delete the file**. Git history is the permanent archive;
we do not keep a parallel graveyard of resolved feedback.

## Retention

None. There is no time-based retention policy. The rule is outcome-based:
a feedback file exists only until its lesson is captured somewhere durable,
then it is removed. To recover a past entry, use `git log -- feedback/`.

## Structure

Files maintain their original naming convention:
- `YYYY-MM-DD-<issue-number>-<short-slug>.yaml`

## See Also

- [Agent Feedback README](../agent-feedback/README.md)
- [Feedback System](../README.md)
