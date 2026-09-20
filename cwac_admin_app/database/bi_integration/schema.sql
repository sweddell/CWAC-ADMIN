-- CWAC Analytics Database Schema V2
-- Enhanced schema with SEO/AEO metrics alongside accessibility
-- SQLite database for comprehensive BI integration

-- ============================================
-- CORE TABLES
-- ============================================

-- Sites table
CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    organisation TEXT,
    sector TEXT,
    group_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES site_groups(id)
);

-- Site groups for comparative reporting
CREATE TABLE IF NOT EXISTS site_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SCAN RESULTS - MAIN TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    scan_id TEXT UNIQUE NOT NULL,
    scan_date TIMESTAMP NOT NULL,
    config_name TEXT,
    
    -- General metrics
    pages_scanned INTEGER DEFAULT 0,
    scan_duration INTEGER,
    
    -- Accessibility metrics
    a11y_score REAL DEFAULT 0,
    a11y_total_issues INTEGER DEFAULT 0,
    a11y_critical_issues INTEGER DEFAULT 0,
    a11y_serious_issues INTEGER DEFAULT 0,
    a11y_moderate_issues INTEGER DEFAULT 0,
    a11y_minor_issues INTEGER DEFAULT 0,
    wcag_level TEXT,
    wcag_version TEXT,
    
    -- SEO/AEO metrics
    seo_score REAL DEFAULT NULL,
    seo_issues_found INTEGER DEFAULT 0,
    seo_title_optimal BOOLEAN DEFAULT NULL,
    seo_meta_desc_optimal BOOLEAN DEFAULT NULL,
    seo_canonical_exists BOOLEAN DEFAULT NULL,
    seo_h1_optimal BOOLEAN DEFAULT NULL,
    seo_alt_coverage REAL DEFAULT NULL,
    seo_json_ld_exists BOOLEAN DEFAULT NULL,
    seo_og_complete BOOLEAN DEFAULT NULL,
    seo_twitter_complete BOOLEAN DEFAULT NULL,
    seo_robots_txt_exists BOOLEAN DEFAULT NULL,
    seo_sitemap_exists BOOLEAN DEFAULT NULL,
    seo_language_tag_exists BOOLEAN DEFAULT NULL,
    seo_internal_links INTEGER DEFAULT NULL,
    seo_external_links INTEGER DEFAULT NULL,
    
    -- Combined score
    combined_score REAL DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id)
);

-- ============================================
-- ACCESSIBILITY DETAILS
-- ============================================

-- Detailed accessibility issue tracking
CREATE TABLE IF NOT EXISTS a11y_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_result_id INTEGER NOT NULL,
    issue_id TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    wcag_criterion TEXT,
    wcag_level TEXT,
    wcag_version TEXT,
    severity TEXT NOT NULL,
    impact TEXT,
    count INTEGER DEFAULT 1,
    pages_affected INTEGER DEFAULT 1,
    description TEXT,
    help_text TEXT,
    help_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE
);

-- Page-level accessibility results
CREATE TABLE IF NOT EXISTS a11y_page_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_result_id INTEGER NOT NULL,
    page_url TEXT NOT NULL,
    page_title TEXT,
    issues_count INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    serious_count INTEGER DEFAULT 0,
    moderate_count INTEGER DEFAULT 0,
    minor_count INTEGER DEFAULT 0,
    load_time REAL,
    response_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE
);

-- ============================================
-- SEO/AEO DETAILS
-- ============================================

-- Page-level SEO metrics
CREATE TABLE IF NOT EXISTS seo_page_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_result_id INTEGER NOT NULL,
    page_url TEXT NOT NULL,
    page_title TEXT,
    
    -- Title optimization
    title_exists BOOLEAN DEFAULT 0,
    title_length INTEGER DEFAULT 0,
    title_optimal BOOLEAN DEFAULT 0,
    
    -- Meta description
    meta_desc_exists BOOLEAN DEFAULT 0,
    meta_desc_length INTEGER DEFAULT 0,
    meta_desc_optimal BOOLEAN DEFAULT 0,
    
    -- Technical SEO
    canonical_exists BOOLEAN DEFAULT 0,
    canonical_url TEXT,
    h1_count INTEGER DEFAULT 0,
    h1_optimal BOOLEAN DEFAULT 0,
    
    -- Content metrics
    images_total INTEGER DEFAULT 0,
    images_with_alt INTEGER DEFAULT 0,
    alt_coverage_percent REAL DEFAULT 0,
    
    -- Structured data
    json_ld_schemas TEXT,
    json_ld_count INTEGER DEFAULT 0,
    
    -- Social meta tags
    og_title BOOLEAN DEFAULT 0,
    og_description BOOLEAN DEFAULT 0,
    og_image BOOLEAN DEFAULT 0,
    og_url BOOLEAN DEFAULT 0,
    og_complete BOOLEAN DEFAULT 0,
    
    twitter_card BOOLEAN DEFAULT 0,
    twitter_title BOOLEAN DEFAULT 0,
    twitter_description BOOLEAN DEFAULT 0,
    twitter_image BOOLEAN DEFAULT 0,
    twitter_complete BOOLEAN DEFAULT 0,
    
    -- Links
    internal_links INTEGER DEFAULT 0,
    external_links INTEGER DEFAULT 0,
    broken_links INTEGER DEFAULT 0,
    
    -- Language
    language_tag TEXT,
    language_tag_exists BOOLEAN DEFAULT 0,
    
    -- Technical files
    robots_txt_exists BOOLEAN DEFAULT 0,
    sitemap_xml_exists BOOLEAN DEFAULT 0,
    
    -- Overall page SEO score
    page_seo_score REAL DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE
);

-- SEO issues/recommendations
CREATE TABLE IF NOT EXISTS seo_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_result_id INTEGER NOT NULL,
    page_url TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    recommendation TEXT,
    impact_score INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE
);

-- ============================================
-- OTHER AUDIT RESULTS
-- ============================================

-- Language audit results
CREATE TABLE IF NOT EXISTS language_audit_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_result_id INTEGER NOT NULL,
    page_url TEXT NOT NULL,
    primary_language TEXT,
    language_confidence REAL,
    reading_level TEXT,
    sentiment_score REAL,
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE
);

-- Reflow audit results
CREATE TABLE IF NOT EXISTS reflow_audit_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_result_id INTEGER NOT NULL,
    page_url TEXT NOT NULL,
    viewport_width INTEGER,
    viewport_height INTEGER,
    overflow_detected BOOLEAN DEFAULT 0,
    overflow_amount INTEGER DEFAULT 0,
    screenshot_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE
);

-- Focus indicator audit results
CREATE TABLE IF NOT EXISTS focus_audit_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_result_id INTEGER NOT NULL,
    page_url TEXT NOT NULL,
    total_elements_tested INTEGER DEFAULT 0,
    elements_with_focus INTEGER DEFAULT 0,
    elements_without_focus INTEGER DEFAULT 0,
    focus_visible_ratio REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE
);

-- ============================================
-- COMPLIANCE & TRENDS
-- ============================================

-- Compliance tracking over time
CREATE TABLE IF NOT EXISTS compliance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    check_date DATE NOT NULL,
    
    -- WCAG Compliance
    wcag_20_a BOOLEAN DEFAULT 0,
    wcag_20_aa BOOLEAN DEFAULT 0,
    wcag_20_aaa BOOLEAN DEFAULT 0,
    wcag_21_a BOOLEAN DEFAULT 0,
    wcag_21_aa BOOLEAN DEFAULT 0,
    wcag_21_aaa BOOLEAN DEFAULT 0,
    wcag_22_a BOOLEAN DEFAULT 0,
    wcag_22_aa BOOLEAN DEFAULT 0,
    wcag_22_aaa BOOLEAN DEFAULT 0,
    
    -- Scores
    a11y_score REAL,
    seo_score REAL,
    combined_score REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id),
    UNIQUE(site_id, check_date)
);

-- Trend analysis (daily aggregates)
CREATE TABLE IF NOT EXISTS daily_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    trend_date DATE NOT NULL,
    
    -- Accessibility trends
    avg_a11y_score REAL,
    total_a11y_issues INTEGER,
    critical_a11y_issues INTEGER,
    
    -- SEO trends
    avg_seo_score REAL,
    total_seo_issues INTEGER,
    avg_alt_coverage REAL,
    
    -- Traffic indicators (if available)
    pages_scanned INTEGER,
    avg_load_time REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(id),
    UNIQUE(site_id, trend_date)
);

-- ============================================
-- GROUP ANALYTICS
-- ============================================

-- Common issues across sites in a group
CREATE TABLE IF NOT EXISTS group_common_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    issue_type TEXT NOT NULL,
    issue_id TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    affected_sites_count INTEGER DEFAULT 0,
    total_occurrences INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES site_groups(id)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Scan results indexes
CREATE INDEX IF NOT EXISTS idx_scan_results_site_id ON scan_results(site_id);
CREATE INDEX IF NOT EXISTS idx_scan_results_scan_date ON scan_results(scan_date);
CREATE INDEX IF NOT EXISTS idx_scan_results_a11y_score ON scan_results(a11y_score);
CREATE INDEX IF NOT EXISTS idx_scan_results_seo_score ON scan_results(seo_score);
CREATE INDEX IF NOT EXISTS idx_scan_results_combined_score ON scan_results(combined_score);

-- Accessibility issue indexes
CREATE INDEX IF NOT EXISTS idx_a11y_issues_scan_result ON a11y_issues(scan_result_id);
CREATE INDEX IF NOT EXISTS idx_a11y_issues_severity ON a11y_issues(severity);
CREATE INDEX IF NOT EXISTS idx_a11y_issues_wcag ON a11y_issues(wcag_criterion);

-- SEO indexes
CREATE INDEX IF NOT EXISTS idx_seo_page_results_scan_result ON seo_page_results(scan_result_id);
CREATE INDEX IF NOT EXISTS idx_seo_page_results_score ON seo_page_results(page_seo_score);
CREATE INDEX IF NOT EXISTS idx_seo_issues_scan_result ON seo_issues(scan_result_id);

-- Other audit indexes
CREATE INDEX IF NOT EXISTS idx_a11y_page_results_scan_result ON a11y_page_results(scan_result_id);
CREATE INDEX IF NOT EXISTS idx_language_results_scan_result ON language_audit_results(scan_result_id);
CREATE INDEX IF NOT EXISTS idx_reflow_results_scan_result ON reflow_audit_results(scan_result_id);
CREATE INDEX IF NOT EXISTS idx_focus_results_scan_result ON focus_audit_results(scan_result_id);

-- Trend indexes
CREATE INDEX IF NOT EXISTS idx_compliance_history_site ON compliance_history(site_id);
CREATE INDEX IF NOT EXISTS idx_compliance_history_date ON compliance_history(check_date);
CREATE INDEX IF NOT EXISTS idx_daily_trends_site ON daily_trends(site_id);
CREATE INDEX IF NOT EXISTS idx_daily_trends_date ON daily_trends(trend_date);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Latest scan for each site
CREATE VIEW IF NOT EXISTS v_latest_scans AS
SELECT 
    s.url,
    s.organisation,
    s.sector,
    sr.*
FROM scan_results sr
INNER JOIN sites s ON sr.site_id = s.id
INNER JOIN (
    SELECT site_id, MAX(scan_date) as max_date
    FROM scan_results
    GROUP BY site_id
) latest ON sr.site_id = latest.site_id AND sr.scan_date = latest.max_date;

-- Site performance summary
CREATE VIEW IF NOT EXISTS v_site_summary AS
SELECT 
    s.id as site_id,
    s.url,
    s.organisation,
    s.sector,
    COUNT(sr.id) as total_scans,
    MAX(sr.scan_date) as last_scan_date,
    AVG(sr.a11y_score) as avg_a11y_score,
    AVG(sr.seo_score) as avg_seo_score,
    AVG(sr.combined_score) as avg_combined_score,
    SUM(sr.a11y_total_issues) as total_a11y_issues,
    SUM(sr.seo_issues_found) as total_seo_issues
FROM sites s
LEFT JOIN scan_results sr ON s.id = sr.site_id
GROUP BY s.id;

-- Accessibility trends
CREATE VIEW IF NOT EXISTS v_a11y_trends AS
SELECT 
    s.url,
    s.organisation,
    DATE(sr.scan_date) as scan_date,
    sr.a11y_score,
    sr.a11y_total_issues,
    sr.a11y_critical_issues,
    sr.a11y_serious_issues,
    sr.wcag_level
FROM scan_results sr
INNER JOIN sites s ON sr.site_id = s.id
WHERE sr.a11y_score IS NOT NULL
ORDER BY s.url, scan_date;

-- SEO trends
CREATE VIEW IF NOT EXISTS v_seo_trends AS
SELECT 
    s.url,
    s.organisation,
    DATE(sr.scan_date) as scan_date,
    sr.seo_score,
    sr.seo_issues_found,
    sr.seo_alt_coverage,
    sr.seo_internal_links,
    sr.seo_external_links
FROM scan_results sr
INNER JOIN sites s ON sr.site_id = s.id
WHERE sr.seo_score IS NOT NULL
ORDER BY s.url, scan_date;

-- Group comparison
CREATE VIEW IF NOT EXISTS v_group_comparison AS
SELECT 
    sg.name as group_name,
    s.url,
    s.organisation,
    sr.a11y_score,
    sr.seo_score,
    sr.combined_score,
    sr.wcag_level,
    sr.a11y_total_issues,
    sr.seo_issues_found,
    sr.scan_date
FROM site_groups sg
INNER JOIN sites s ON s.group_id = sg.id
INNER JOIN scan_results sr ON sr.site_id = s.id
WHERE sr.id IN (
    SELECT id FROM v_latest_scans
)
ORDER BY sg.name, sr.combined_score DESC;

-- Top accessibility issues
CREATE VIEW IF NOT EXISTS v_top_a11y_issues AS
SELECT 
    ai.issue_id,
    ai.issue_type,
    ai.wcag_criterion,
    ai.wcag_level,
    ai.severity,
    COUNT(DISTINCT ai.scan_result_id) as scans_affected,
    SUM(ai.count) as total_occurrences,
    SUM(ai.pages_affected) as total_pages_affected,
    ai.description,
    ai.help_url
FROM a11y_issues ai
GROUP BY ai.issue_id, ai.wcag_criterion
ORDER BY total_occurrences DESC
LIMIT 50;

-- Top SEO issues
CREATE VIEW IF NOT EXISTS v_top_seo_issues AS
SELECT 
    si.issue_type,
    si.severity,
    COUNT(DISTINCT si.scan_result_id) as scans_affected,
    COUNT(*) as total_occurrences,
    si.description,
    si.recommendation
FROM seo_issues si
GROUP BY si.issue_type, si.severity
ORDER BY total_occurrences DESC
LIMIT 50;

-- Combined score leaderboard
CREATE VIEW IF NOT EXISTS v_leaderboard AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY sr.combined_score DESC) as rank,
    s.url,
    s.organisation,
    sr.combined_score,
    sr.a11y_score,
    sr.seo_score,
    sr.wcag_level,
    sr.scan_date
FROM v_latest_scans sr
INNER JOIN sites s ON sr.site_id = s.id
WHERE sr.combined_score IS NOT NULL
ORDER BY sr.combined_score DESC;

-- ============================================
-- SYSTEM MANAGEMENT TABLES
-- ============================================

-- Scan schedules for automated scanning
CREATE TABLE IF NOT EXISTS scan_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name TEXT NOT NULL,
    config_path TEXT NOT NULL,
    schedule_type TEXT NOT NULL,  -- 'hourly', 'daily', 'weekly', 'monthly', 'cron'
    schedule_value TEXT NOT NULL, -- e.g., '2' for hourly, '09:00' for daily, 'monday,09:00' for weekly
    enabled INTEGER DEFAULT 1,
    last_run TEXT,
    next_run TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Activity log for tracking user actions and system events
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,     -- 'scan_start', 'scan_complete', 'user_login', 'config_change', etc.
    event_name TEXT,
    details TEXT,
    scan_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System metadata for configuration and status
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Scan results indexes
CREATE INDEX IF NOT EXISTS idx_scan_results_site_id ON scan_results(site_id);
CREATE INDEX IF NOT EXISTS idx_scan_results_scan_date ON scan_results(scan_date);
CREATE INDEX IF NOT EXISTS idx_scan_results_scan_id ON scan_results(scan_id);

-- Activity log indexes
CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON activity_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_event_type ON activity_log(event_type);
CREATE INDEX IF NOT EXISTS idx_activity_log_scan_id ON activity_log(scan_id);

-- Scan schedules indexes
CREATE INDEX IF NOT EXISTS idx_scan_schedules_enabled ON scan_schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_scan_schedules_next_run ON scan_schedules(next_run);
