# CWAC-ADMIN Scoring System

Complete guide to understanding how CWAC-ADMIN calculates accessibility scores and determines WCAG compliance levels.

---

## Overview

CWAC-ADMIN uses a **severity-weighted penalty system** to calculate accessibility scores. This approach ensures that critical accessibility issues have a significantly greater impact on the score than minor issues, reflecting their real-world impact on users with disabilities.

---

## Score Calculation Formula

### Page-Level Scoring

Each page is scored independently using the following formula:

```
penalty = (critical_issues × 10) + (serious_issues × 5) + (moderate_issues × 2) + (minor_issues × 1)

page_score = max(0, 100 - min(100, penalty))
```

**Key Points:**
- Scores range from 0 to 100
- Perfect score (100) means zero issues detected
- Score cannot go below 0 or above 100
- Each severity level has a different weight

### Site-Level Scoring

The site score is the **average of all page scores**:

```
site_score = sum(page_scores) / number_of_pages
```

**Why averaging?**
- Reflects overall site accessibility
- Balances good and poor pages
- Prevents one bad page from dominating the score
- Encourages fixing issues across all pages

---

## Severity Weights Explained

### Weight Distribution

| Severity | Weight | Rationale |
|----------|--------|-----------|
| **Critical** | 10 points | Complete barriers to access for users with disabilities. Must be fixed immediately. |
| **Serious** | 5 points | Significant obstacles that severely impact usability. High priority fixes. |
| **Moderate** | 2 points | Noticeable issues that create difficulties for some users. Should be addressed. |
| **Minor** | 1 point | Best practice violations with minimal user impact. Nice to fix when possible. |

### Why These Weights?

1. **Critical = 10×**: Critical issues like missing alt text or keyboard traps can completely prevent access
2. **Serious = 5×**: Half the impact of critical but still creates major barriers
3. **Moderate = 2×**: Twice the impact of minor issues, noticeable problems
4. **Minor = 1×**: Baseline weight for best practice improvements

---

## Worked Examples

### Example 1: Good Site

**Page 1:**
- 0 critical, 0 serious, 1 moderate, 3 minor
- penalty = (0 × 10) + (0 × 5) + (1 × 2) + (3 × 1) = 5
- page_score = 100 - 5 = **95**

**Page 2:**
- 0 critical, 0 serious, 0 moderate, 2 minor
- penalty = (0 × 10) + (0 × 5) + (0 × 2) + (2 × 1) = 2
- page_score = 100 - 2 = **98**

**Page 3:**
- 0 critical, 0 serious, 2 moderate, 1 minor
- penalty = (0 × 10) + (0 × 5) + (2 × 2) + (1 × 1) = 5
- page_score = 100 - 5 = **95**

**Site Score = (95 + 98 + 95) / 3 = 96.0**
**WCAG Level: WCAG 2.2 AAA** ✅

---

### Example 2: Fair Site

**Page 1:**
- 1 critical, 2 serious, 3 moderate, 5 minor
- penalty = (1 × 10) + (2 × 5) + (3 × 2) + (5 × 1) = 31
- page_score = 100 - 31 = **69**

**Page 2:**
- 0 critical, 3 serious, 5 moderate, 8 minor
- penalty = (0 × 10) + (3 × 5) + (5 × 2) + (8 × 1) = 33
- page_score = 100 - 33 = **67**

**Page 3:**
- 2 critical, 1 serious, 2 moderate, 4 minor
- penalty = (2 × 10) + (1 × 5) + (2 × 2) + (4 × 1) = 33
- page_score = 100 - 33 = **67**

**Site Score = (69 + 67 + 67) / 3 = 67.7**
**WCAG Level: Non-compliant** ❌

---

### Example 3: Mixed Quality

**Page 1 (Perfect):**
- 0 critical, 0 serious, 0 moderate, 0 minor
- penalty = 0
- page_score = 100 - 0 = **100**

**Page 2 (Good):**
- 0 critical, 1 serious, 2 moderate, 3 minor
- penalty = (0 × 10) + (1 × 5) + (2 × 2) + (3 × 1) = 12
- page_score = 100 - 12 = **88**

**Page 3 (Poor):**
- 3 critical, 2 serious, 5 moderate, 10 minor
- penalty = (3 × 10) + (2 × 5) + (5 × 2) + (10 × 1) = 60
- page_score = 100 - 60 = **40**

**Site Score = (100 + 88 + 40) / 3 = 76.0**
**WCAG Level: Non-compliant** ⚠️

*Even with one perfect page, critical issues on other pages bring down the site score.*

---

## WCAG Compliance Determination

### Automatic Level Assignment

WCAG compliance is determined by the **presence or absence** of issues by severity:

```python
if critical == 0 and serious == 0 and moderate == 0:
    level = "WCAG 2.2 AAA"
elif critical == 0 and serious == 0:
    level = "WCAG 2.2 AA"
elif critical == 0:
    level = "WCAG 2.2 A"
else:
    level = "Non-compliant"
```

### Compliance Requirements

| WCAG Level | Critical | Serious | Moderate | Typical Score |
|------------|----------|---------|----------|---------------|
| **WCAG 2.2 AAA** | ✅ 0 | ✅ 0 | ✅ 0 | 95-100 |
| **WCAG 2.2 AA** | ✅ 0 | ✅ 0 | ⚠️ Any | 90-94 |
| **WCAG 2.2 A** | ✅ 0 | ⚠️ Any | ⚠️ Any | 80-89 |
| **Non-compliant** | ❌ 1+ | ⚠️ Any | ⚠️ Any | Below 80 |

### Cascading Compliance

WCAG standards are cumulative. Meeting a higher level means you also meet all lower levels:

**WCAG 2.2 AAA includes:**
- ✅ WCAG 2.2 AA
- ✅ WCAG 2.2 A
- ✅ WCAG 2.1 AAA
- ✅ WCAG 2.1 AA
- ✅ WCAG 2.1 A
- ✅ WCAG 2.0 AAA
- ✅ WCAG 2.0 AA
- ✅ WCAG 2.0 A

**WCAG 2.2 AA includes:**
- ✅ WCAG 2.2 A
- ✅ WCAG 2.1 AA
- ✅ WCAG 2.1 A
- ✅ WCAG 2.0 AA
- ✅ WCAG 2.0 A

---

## Score Interpretation Guide

### Score Ranges

| Score | Rating | Meaning | Action Required |
|-------|--------|---------|-----------------|
| **95-100** | ⭐⭐⭐⭐⭐ Excellent | Outstanding accessibility. Only minor issues if any. | Maintain standards, periodic reviews |
| **90-94** | ⭐⭐⭐⭐ Good | Meets WCAG AA. Some moderate issues present. | Review moderate issues, aim for AAA |
| **80-89** | ⭐⭐⭐ Fair | Meets WCAG A. Serious issues require attention. | Address serious issues immediately |
| **70-79** | ⭐⭐ Poor | Significant barriers exist for users. | Urgent fixes needed for serious issues |
| **60-69** | ⭐ Very Poor | Major accessibility problems throughout. | Complete accessibility audit required |
| **Below 60** | ❌ Critical | Severe accessibility barriers. Site may be unusable. | Emergency remediation, may face legal risks |

### Color Coding

Scores are typically displayed with color indicators:

- 🟢 **Green (90+)**: WCAG AA or better
- 🟡 **Yellow (80-89)**: WCAG A level
- 🟠 **Orange (70-79)**: Below WCAG standards
- 🔴 **Red (Below 70)**: Critical accessibility issues

---

## Common Issue Examples

### Critical Issues (10 points each)

Examples that typically receive "critical" severity:
- Images missing alt text
- Forms without labels
- Insufficient color contrast (< 3:1)
- Keyboard traps
- Missing page language
- Inaccessible CAPTCHA
- Auto-playing audio/video
- Time limits without ability to extend

**Impact:** Complete barriers to access for users with disabilities.

### Serious Issues (5 points each)

Examples that typically receive "serious" severity:
- Missing form field labels
- Insufficient focus indicators
- Skip navigation links missing
- Heading structure problems
- ARIA label conflicts
- Buttons without accessible names
- Missing table headers
- Inadequate touch target sizes

**Impact:** Significant obstacles that severely impact usability.

### Moderate Issues (2 points each)

Examples that typically receive "moderate" severity:
- Missing page titles
- Unclear link text
- Redundant ARIA attributes
- Non-descriptive button text
- Missing landmark regions
- Inconsistent navigation
- No visible focus on some elements

**Impact:** Noticeable issues that create difficulties for some users.

### Minor Issues (1 point each)

Examples that typically receive "minor" severity:
- Missing language attributes on elements
- Redundant alternative text
- Empty headings
- Deprecated HTML attributes
- Best practice ARIA usage
- Semantic HTML improvements
- Minor contrast issues (4.5:1 vs 7:1)

**Impact:** Best practice violations with minimal direct user impact.

---

## Frequently Asked Questions

### Why not just count total issues?

Counting all issues equally would treat a missing alt text (critical) the same as a redundant link (minor). Our weighted system reflects the real-world impact on users with disabilities.

### Can a site score 100?

Yes! A perfect score of 100 means zero accessibility issues were detected. However, remember that automated testing catches only 30-40% of all accessibility issues. Manual testing is still required.

### Why does averaging page scores matter?

If we summed penalties across all pages, sites with more pages would be unfairly penalized. Averaging ensures fair comparison between sites regardless of size.

### What if a page has 100+ issues?

The penalty is capped at 100 points, so the minimum score is 0. This prevents scores from going negative.

### How do I improve my score?

Priority order:
1. **Fix critical issues first** - Biggest impact on score and users
2. **Address serious issues** - Next priority for compliance
3. **Review moderate issues** - Improve user experience
4. **Clean up minor issues** - Polish and best practices

### Is this scoring system standard?

Our formula is custom-designed for CWAC-ADMIN, but the severity classifications come directly from axe-core and align with WCAG guidelines. The weights reflect real-world user impact.

### Can I customize the weights?

The weights are hardcoded based on accessibility research and best practices. Customizing them could lead to scores that don't reflect actual user impact.

---

## Technical Implementation

### Where Scoring Happens

Scoring is calculated in:
- `cwac_admin_app/database/bi_integration/comprehensive_sync.py`
- Function: `parse_scan_results()`
- Lines: 179-198

### Database Storage

Scores are stored in the `scan_results` table:
- `a11y_score` - Overall accessibility score (0-100)
- `a11y_total_issues` - Total unique issues found
- `a11y_critical_issues` - Count of critical issues
- `a11y_serious_issues` - Count of serious issues
- `a11y_moderate_issues` - Count of moderate issues
- `a11y_minor_issues` - Count of minor issues

### API Access

Retrieve scores via API:
```bash
GET /api/sites/{id}/scans
GET /api/scans/{scan_id}
GET /api/dashboard/metrics
```

---

## Best Practices

### For Site Owners

1. **Target 90+**: Aim for WCAG AA compliance minimum
2. **Fix critical first**: Maximum impact on score and users
3. **Monitor trends**: Track scores over time
4. **Regular scans**: Schedule monthly or after major updates
5. **Manual testing**: Automated tests catch only 30-40% of issues

### For Developers

1. **Test early**: Integrate accessibility testing in development
2. **Use semantic HTML**: Reduces many common issues
3. **ARIA carefully**: Only when semantic HTML isn't enough
4. **Keyboard test**: All functionality accessible via keyboard
5. **Color contrast**: Use tools to verify sufficient contrast

### For Accessibility Teams

1. **Prioritize by severity**: Critical → Serious → Moderate → Minor
2. **Track over time**: Use historical data to measure progress
3. **Compare sites**: Identify best practices from high-scoring sites
4. **Educate teams**: Share scoring system with developers
5. **Complement automated**: Combine with manual testing and user research

---

## Related Documentation

- [Admin Interface Guide](admin-interface.md) - View scores in the dashboard
- [Database Schema](database-schema.md) - Where scores are stored
- [API Reference](api-reference.md) - Retrieve scores programmatically
- [Troubleshooting](troubleshooting.md) - Common scoring questions

---

**Remember:** A high score is excellent, but it doesn't guarantee complete accessibility. Always combine automated testing with manual testing and user feedback for comprehensive accessibility assurance.
