# EHRBase Issues Tracker

This directory tracks issues we've discovered with EHRBase that may need to be reported upstream or are awaiting fixes.

## Issue Status Key

- 🔴 **Not Reported** - Issue discovered but not yet reported to EHRBase
- 🟡 **Reported** - GitHub issue filed, awaiting response
- 🟢 **Acknowledged** - EHRBase team has acknowledged the issue
- 🔵 **Fixed** - Issue has been fixed in EHRBase
- ⚪ **Won't Fix** - Issue closed as "won't fix" or "working as intended"

---

## Active Issues

### 🔴 [001-flat-format-documentation-gap.md](001-flat-format-documentation-gap.md)
**Status:** Not Reported
**Severity:** High (blocks new users)
**Summary:** FLAT format structure changed in EHRBase 2.0 but documentation still shows old format

---

## Guidelines

### When to Create an Issue Document

Create a new issue document when you discover:
1. **Documentation gaps** - Docs don't match implementation
2. **API bugs** - Endpoints behaving incorrectly
3. **Breaking changes** - Undocumented changes between versions
4. **Missing features** - Expected functionality not implemented
5. **Validation problems** - EHRBase rejecting valid data

### How to Name Issue Files

Use format: `NNN-short-description.md`
- `NNN` = Sequential number (001, 002, 003...)
- `short-description` = kebab-case brief description
- Examples:
  - `001-flat-format-documentation-gap.md`
  - `002-composition-update-http-405.md`
  - `003-ehr-status-missing-archetype-node-id.md`

### Issue Document Template

```markdown
# Issue: [Title]

**Status:** 🔴 Not Reported
**Discovered:** YYYY-MM-DD
**Affects:** EHRBase X.Y.Z+
**Severity:** [Low/Medium/High/Critical]

## Summary

Brief description of the issue.

## Impact

Who is affected and how?

## Evidence

### Expected Behavior
What should happen according to specs/docs?

### Actual Behavior
What actually happens?

### Reproduction
Steps to reproduce the issue.

### Supporting Information
- Links to documentation
- Error messages
- Code examples
- API responses

## Workaround

How we're working around this issue in our SDK.

## Upstream Tracking

- [ ] GitHub Issue Created: [#NNNN](link)
- [ ] Discourse Discussion: [link](link)
- [ ] EHRBase Response: [date] - response summary
- [ ] Fix Released: [version]

## Related

- Related issues in this directory
- Related SDK code files
- Related documentation
```

---

## Reporting Process

### Before Reporting

1. ✅ **Verify the issue** - Test against latest EHRBase version
2. ✅ **Search existing issues** - Check if already reported
3. ✅ **Document thoroughly** - Create issue document here
4. ✅ **Prepare reproduction** - Minimal example that demonstrates issue

### When Reporting

1. **Choose platform:**
   - **GitHub Issues:** For bugs, API problems, missing features
   - **Discourse:** For questions, documentation gaps, design discussions

2. **Create GitHub issue:**
   - Use clear, descriptive title
   - Reference our issue document
   - Provide minimal reproduction case
   - Link to our documentation if we've solved it

3. **Update our tracker:**
   - Change status to 🟡 Reported
   - Add GitHub issue link
   - Add date reported

### After Reporting

1. **Monitor responses** - Update issue document with EHRBase team responses
2. **Update status** - Change status as issue progresses
3. **Update workarounds** - If EHRBase suggests better workarounds
4. **Celebrate fixes** - Mark as 🔵 Fixed when released

---

## Issue Index

| # | Title | Status | Severity | Reported | Fixed |
|---|-------|--------|----------|----------|-------|
| 001 | FLAT format documentation gap | 🔴 Not Reported | High | - | - |

---

## Statistics

- **Total Issues:** 1
- **Not Reported:** 1
- **Reported:** 0
- **Acknowledged:** 0
- **Fixed:** 0
- **Won't Fix:** 0

---

**Last Updated:** 2026-01-09
