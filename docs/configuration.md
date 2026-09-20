# Scan Configuration Guide

Complete guide to configuring accessibility scans in CWAC-ADMIN.

## Overview

Scan configurations define how the CWAC scanner tests your websites for accessibility. This guide covers:

- Configuration file format
- Available settings and options
- Creating custom configurations
- Best practices for different use cases

## Configuration File Format

Scan configurations are stored as JSON files in the `config/` directory.

### Basic Structure

```json
{
  "base_urls": [
    "https://www.example.com"
  ],
  "user_agent": "CWAC-ADMIN/1.0",
  "max_pages": 20,
  "crawl_delay": 1.0,
  "respect_robots_txt": true,
  "wcag_version": "WCAG22",
  "wcag_level": "AA",
  "audits": {
    "language_audit": true,
    "reflow_audit": true,
    "focus_indicator_audit": true
  },
  "screenshot_audits": {
    "enabled": true
  }
}
```

## Configuration Options

### Base URLs

**`base_urls`** (array, required)

List of websites to scan.

```json
{
  "base_urls": [
    "https://www.example.com",
    "https://www.another-site.org"
  ]
}
```

**Options:**
- Single URL for focused scans
- Multiple URLs for batch scanning
- Include `https://` or `http://` protocol

### Crawler Settings

**`max_pages`** (integer, default: 20)

Maximum number of pages to scan per site.

```json
{
  "max_pages": 50
}
```

**Recommendations:**
- **Quick test:** 5-10 pages
- **Standard scan:** 20-50 pages
- **Comprehensive:** 100+ pages
- **Full site:** Set high limit or 0 for unlimited (use with caution)

---

**`crawl_delay`** (float, default: 1.0)

Delay in seconds between page requests.

```json
{
  "crawl_delay": 2.0
}
```

**Recommendations:**
- **Fast:** 0.5-1.0 seconds (for test environments)
- **Normal:** 1.0-2.0 seconds (recommended)
- **Polite:** 2.0-5.0 seconds (for production sites)

---

**`respect_robots_txt`** (boolean, default: true)

Whether to respect robots.txt rules.

```json
{
  "respect_robots_txt": false
}
```

**Use `false` when:**
- Testing internal/development sites
- Site's robots.txt is overly restrictive
- You own the site being tested

**Use `true` when:**
- Scanning third-party websites
- Following web etiquette
- Avoiding crawler blocks

### User Agent

**`user_agent`** (string, default: "CWAC-ADMIN/1.0")

Custom user agent string for requests.

```json
{
  "user_agent": "CWAC-ADMIN/1.0 (MyCompany Accessibility Team)"
}
```

**Best Practices:**
- Include "CWAC-ADMIN" for identification
- Add your organization name
- Include contact info (optional)

### WCAG Settings

**`wcag_version`** (string, default: "WCAG22")

WCAG version to test against.

```json
{
  "wcag_version": "WCAG22"
}
```

**Options:**
- `"WCAG20"` - WCAG 2.0 (older standard)
- `"WCAG21"` - WCAG 2.1 (current standard)
- `"WCAG22"` - WCAG 2.2 (latest standard, recommended)

---

**`wcag_level`** (string, default: "AA")

WCAG conformance level to test.

```json
{
  "wcag_level": "AAA"
}
```

**Options:**
- `"A"` - Minimum level (basic accessibility)
- `"AA"` - Standard level (recommended for most organizations)
- `"AAA"` - Enhanced level (highest accessibility)

**Recommendations:**
- **Government sites:** AA minimum, AAA preferred
- **Commercial sites:** AA (legal requirement in many jurisdictions)
- **Education sites:** AA minimum
- **Testing/Development:** Start with AA

### Custom Audits

**`audits`** (object)

Enable or disable custom audit plugins.

```json
{
  "audits": {
    "language_audit": true,
    "reflow_audit": true,
    "focus_indicator_audit": true
  }
}
```

#### Available Audits

**`language_audit`** (boolean, default: true)

Tests for proper HTML `lang` attribute.

- Checks if `<html lang="...">` is present
- Validates language code (e.g., "en", "es", "fr")
- Ensures lang attribute matches content language

**`reflow_audit`** (boolean, default: true)

Tests responsive design and content reflow.

- Tests at 320px width (mobile viewport)
- Checks for horizontal scrolling
- Validates content fits viewport
- Tests WCAG 2.1 Success Criterion 1.4.10 (Reflow)

**`focus_indicator_audit`** (boolean, default: true)

Tests keyboard focus visibility.

- Checks focus indicators on interactive elements
- Measures contrast ratio of focus indicators
- Validates WCAG 2.4.7 (Focus Visible)
- Tests keyboard navigation

### Screenshot Audits

**`screenshot_audits`** (object)

Configure screenshot capture during scans.

```json
{
  "screenshot_audits": {
    "enabled": true,
    "capture_type": "viewport",
    "viewports": [
      {"width": 1920, "height": 1080},
      {"width": 768, "height": 1024},
      {"width": 375, "height": 667}
    ]
  }
}
```

**Options:**
- **`enabled`**: Enable/disable screenshots
- **`capture_type`**: "viewport", "full-page", or "element"
- **`viewports`**: Array of viewport sizes to test

### Advanced Options

**`timeout`** (integer, default: 30)

Page load timeout in seconds.

```json
{
  "timeout": 60
}
```

---

**`exclude_patterns`** (array)

URL patterns to skip during crawling.

```json
{
  "exclude_patterns": [
    "*/admin/*",
    "*/login*",
    "*/api/*",
    "*.pdf"
  ]
}
```

---

**`include_patterns`** (array)

Only crawl URLs matching these patterns.

```json
{
  "include_patterns": [
    "*/products/*",
    "*/services/*"
  ]
}
```

---

**`max_depth`** (integer)

Maximum link depth from base URL.

```json
{
  "max_depth": 3
}
```

**Example:**
- Depth 0: Base URL only
- Depth 1: Base URL + pages linked from it
- Depth 2: Above + pages linked from those
- Depth 3: And so on...

---

**`follow_external_links`** (boolean, default: false)

Whether to follow links to external domains.

```json
{
  "follow_external_links": false
}
```

---

**`headless`** (boolean, default: true)

Run browser in headless mode (no GUI).

```json
{
  "headless": false
}
```

Set to `false` for debugging purposes.

## Configuration Examples

### Example 1: Quick Homepage Test

Test only the homepage with basic audits.

```json
{
  "base_urls": ["https://www.example.com"],
  "max_pages": 1,
  "crawl_delay": 0.5,
  "wcag_version": "WCAG22",
  "wcag_level": "AA",
  "audits": {
    "language_audit": true,
    "reflow_audit": false,
    "focus_indicator_audit": false
  }
}
```

**Use case:** Quick smoke test during development

### Example 2: Standard Site Scan

Balanced scan for regular monitoring.

```json
{
  "base_urls": ["https://www.example.com"],
  "max_pages": 20,
  "crawl_delay": 1.0,
  "respect_robots_txt": true,
  "wcag_version": "WCAG22",
  "wcag_level": "AA",
  "audits": {
    "language_audit": true,
    "reflow_audit": true,
    "focus_indicator_audit": true
  },
  "screenshot_audits": {
    "enabled": true
  }
}
```

**Use case:** Regular scheduled scans

### Example 3: Comprehensive Audit

Deep scan with all audits enabled.

```json
{
  "base_urls": ["https://www.example.com"],
  "max_pages": 100,
  "crawl_delay": 2.0,
  "respect_robots_txt": true,
  "wcag_version": "WCAG22",
  "wcag_level": "AAA",
  "max_depth": 5,
  "audits": {
    "language_audit": true,
    "reflow_audit": true,
    "focus_indicator_audit": true
  },
  "screenshot_audits": {
    "enabled": true,
    "capture_type": "full-page",
    "viewports": [
      {"width": 1920, "height": 1080},
      {"width": 1366, "height": 768},
      {"width": 768, "height": 1024},
      {"width": 375, "height": 667}
    ]
  },
  "timeout": 60
}
```

**Use case:** Pre-launch comprehensive audit

### Example 4: Multi-Site Batch Scan

Scan multiple related sites at once.

```json
{
  "base_urls": [
    "https://www.site1.com",
    "https://www.site2.com",
    "https://www.site3.com"
  ],
  "max_pages": 10,
  "crawl_delay": 1.5,
  "wcag_version": "WCAG22",
  "wcag_level": "AA",
  "audits": {
    "language_audit": true,
    "reflow_audit": true,
    "focus_indicator_audit": true
  }
}
```

**Use case:** Compare accessibility across a portfolio of sites

### Example 5: Focused Section Test

Test only specific section of a site.

```json
{
  "base_urls": ["https://www.example.com/products"],
  "max_pages": 30,
  "crawl_delay": 1.0,
  "include_patterns": ["*/products/*"],
  "exclude_patterns": [
    "*/products/admin/*",
    "*/products/api/*"
  ],
  "wcag_version": "WCAG22",
  "wcag_level": "AA",
  "audits": {
    "language_audit": true,
    "reflow_audit": true,
    "focus_indicator_audit": true
  }
}
```

**Use case:** Test specific section after updates

## Creating Configurations

### Method 1: Via Admin Interface

1. Go to **Scan** → **Configurations** tab
2. Click **"+ Add Configuration"**
3. Fill in the form or upload JSON file
4. Click **"Save"**

### Method 2: Create JSON File Manually

1. Create a new file in `config/` directory
2. Name it descriptively (e.g., `config_daily_full_scan.json`)
3. Add your configuration JSON
4. Save the file
5. Refresh admin interface to see it in the list

### Method 3: Duplicate and Modify

1. Copy an existing config file
2. Rename it
3. Modify settings as needed
4. Save

## Best Practices

### Performance Optimization

**For faster scans:**
- Reduce `max_pages` (test fewer pages)
- Decrease `crawl_delay` (0.5-1.0 seconds)
- Disable non-essential audits
- Disable screenshots
- Use `max_depth` to limit crawling

**For thorough audits:**
- Increase `max_pages`
- Enable all audits
- Enable screenshots
- Test multiple viewports
- Increase `timeout` for slow pages

### Scan Frequency Recommendations

**Homepage only:**
- After every deployment
- Daily during active development

**Standard scan (20 pages):**
- Daily for critical sites
- Weekly for standard sites
- Monthly for low-traffic sites

**Comprehensive scan (100+ pages):**
- Weekly for critical sites
- Monthly for standard sites
- Quarterly for stable sites

### WCAG Level Selection

**When to use Level A:**
- Initial accessibility assessment
- Sites with known major issues
- Legacy applications

**When to use Level AA (recommended):**
- Most organizations should target AA
- Legal compliance (WCAG 2.1 AA is often required)
- Balanced accessibility and feasibility

**When to use Level AAA:**
- Government sites with high accessibility requirements
- Sites serving users with disabilities specifically
- Organizations committed to maximum accessibility
- Note: Full AAA compliance may not be possible for all content

### Respect for Target Sites

**Always:**
- Use appropriate `crawl_delay` (1.0+ seconds)
- Respect `robots.txt` for external sites
- Scan during off-peak hours
- Include contact info in user agent

**Never:**
- Hammer sites with rapid requests
- Ignore robots.txt on sites you don't own
- Scan without permission for third-party sites
- Use scan tool for malicious purposes

## Troubleshooting

### Configuration Not Appearing

**Problem:** Created config file but it doesn't appear in admin interface

**Solutions:**
- Check file extension is `.json`
- Validate JSON syntax (use JSONLint.com)
- Ensure file is in `config/` directory
- Refresh browser page
- Check file permissions

### Scan Times Out

**Problem:** Scans fail with timeout errors

**Solutions:**
- Increase `timeout` value (e.g., 60 seconds)
- Reduce `max_pages`
- Check target site's response time
- Verify network connectivity

### Pages Being Skipped

**Problem:** Scanner skips pages you want to test

**Solutions:**
- Check `exclude_patterns` - ensure patterns don't match desired pages
- Review `include_patterns` - ensure patterns match desired pages
- Check `max_depth` - increase if pages are deeply nested
- Verify `respect_robots_txt` - set to false if robots.txt is blocking

### Inconsistent Results

**Problem:** Different scans show different results

**Solutions:**
- Use consistent configuration settings
- Ensure site hasn't changed between scans
- Check if dynamic content affects results
- Increase `crawl_delay` if rate-limiting is occurring

## Configuration Validation

### Validate JSON Syntax

```bash
# Using Python
python3 -m json.tool config/my_config.json

# Using jq (if installed)
jq . config/my_config.json
```

### Test Configuration

Before scheduling, test your configuration:

1. Go to **Scan** page
2. Select your configuration
3. Click **"Start Scan"**
4. Monitor progress
5. Review results
6. Adjust configuration if needed

## Advanced Configuration

### Custom Audit Plugins

To add custom audits, place Python files in `cwac_admin_app/plugins/`:

```python
# cwac_admin_app/plugins/my_custom_audit.py
from cwac.src.audits.base import BaseAudit

class MyCustomAudit(BaseAudit):
    def run(self, driver, page_url):
        # Your audit logic
        return {
            "passed": True,
            "issues": []
        }
```

Then enable in configuration:

```json
{
  "audits": {
    "my_custom_audit": true
  }
}
```

### Environment-Specific Configs

Create configs for different environments:

```
config/
├── production_full_scan.json
├── staging_quick_test.json
├── development_homepage.json
└── ci_automated_scan.json
```

## Next Steps

- Create your first configuration using examples above
- Test it with a manual scan
- Review the [Scheduling Guide](scheduling.md) to automate scans
- Check [Troubleshooting](troubleshooting.md) if you encounter issues

## Reference

- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [Scan Scheduling](scheduling.md)
- [Admin Interface Guide](admin-interface.md)
- [API Reference](api-reference.md)
