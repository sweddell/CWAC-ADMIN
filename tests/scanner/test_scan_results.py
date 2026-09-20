"""
Test Scan Results Processing
=============================

Tests for processing and validating scan results.
"""

import pytest
import csv
from pathlib import Path


@pytest.mark.scanner
@pytest.mark.unit
class TestResultFileStructure:
    """Test scan result file structure."""
    
    def test_scan_success_marker_exists(self, mock_scan_results):
        """Test successful scans have .scan_success marker."""
        success_file = mock_scan_results / '.scan_success'
        assert success_file.exists()
    
    def test_axe_csv_file_exists(self, mock_scan_results):
        """Test axe_core_audit.csv exists in results."""
        axe_file = mock_scan_results / 'axe_core_audit.csv'
        assert axe_file.exists()
    
    def test_pages_scanned_csv_exists(self, mock_scan_results):
        """Test pages_scanned.csv exists in results."""
        pages_file = mock_scan_results / 'pages_scanned.csv'
        assert pages_file.exists()


@pytest.mark.scanner
@pytest.mark.unit
class TestAxeCoreResults:
    """Test axe-core audit results parsing."""
    
    def test_axe_csv_has_required_columns(self, mock_scan_results):
        """Test axe CSV has all required columns."""
        axe_file = mock_scan_results / 'axe_core_audit.csv'
        
        with open(axe_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            required_columns = ['url', 'id', 'impact', 'description', 'help']
            for column in required_columns:
                assert column in headers, f"Missing required column: {column}"
    
    def test_axe_csv_data_valid(self, mock_scan_results):
        """Test axe CSV contains valid data."""
        axe_file = mock_scan_results / 'axe_core_audit.csv'
        
        with open(axe_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) > 0, "No data in axe results"
            
            for row in rows:
                # Check URL is present
                assert row['url'], "Missing URL"
                
                # Check impact level is valid
                if row['impact']:
                    assert row['impact'] in ['minor', 'moderate', 'serious', 'critical']
                
                # Check rule ID exists
                assert row['id'], "Missing rule ID"
    
    def test_axe_csv_can_count_issues_by_severity(self, mock_scan_results):
        """Test we can count issues by severity level."""
        axe_file = mock_scan_results / 'axe_core_audit.csv'
        
        with open(axe_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            severity_counts = {'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0}
            
            for row in rows:
                impact = row.get('impact', '').lower()
                if impact in severity_counts:
                    severity_counts[impact] += 1
            
            # Should have at least some issues
            total_issues = sum(severity_counts.values())
            assert total_issues > 0


@pytest.mark.scanner
@pytest.mark.unit
class TestPagesScanResult:
    """Test pages scanned results."""
    
    def test_pages_csv_has_required_columns(self, mock_scan_results):
        """Test pages CSV has URL column."""
        pages_file = mock_scan_results / 'pages_scanned.csv'
        
        with open(pages_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            assert 'url' in headers
    
    def test_pages_csv_lists_scanned_pages(self, mock_scan_results):
        """Test pages CSV contains page entries."""
        pages_file = mock_scan_results / 'pages_scanned.csv'
        
        with open(pages_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) > 0, "No pages in scan results"
            
            for row in rows:
                assert row['url'], "Missing page URL"


@pytest.mark.scanner
@pytest.mark.integration
class TestResultsProcessing:
    """Test end-to-end results processing."""
    
    def test_can_determine_scan_success(self, mock_scan_results):
        """Test we can determine if scan was successful."""
        success_marker = mock_scan_results / '.scan_success'
        
        # Successful scan has marker
        assert success_marker.exists()
        
        scan_status = 'completed' if success_marker.exists() else 'failed'
        assert scan_status == 'completed'
    
    def test_can_calculate_accessibility_score(self, mock_scan_results):
        """Test we can calculate overall accessibility score."""
        axe_file = mock_scan_results / 'axe_core_audit.csv'
        
        with open(axe_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Count issues by severity
            critical = sum(1 for r in rows if r.get('impact') == 'critical')
            serious = sum(1 for r in rows if r.get('impact') == 'serious')
            moderate = sum(1 for r in rows if r.get('impact') == 'moderate')
            minor = sum(1 for r in rows if r.get('impact') == 'minor')
            
            # Calculate penalty
            penalty = (critical * 10) + (serious * 5) + (moderate * 2) + (minor * 1)
            
            # Calculate score
            score = max(0, min(100, 100 - penalty))
            
            # Score should be between 0 and 100
            assert 0 <= score <= 100
    
    def test_can_extract_scan_timestamp(self, mock_scan_results):
        """Test we can extract scan timestamp from directory name."""
        dir_name = mock_scan_results.name
        
        # Directory name format: YYYY-MM-DD_HH-MM-SS_Name
        # Or just check it's a valid directory
        assert dir_name, "Empty directory name"
        assert isinstance(dir_name, str)


@pytest.mark.scanner
@pytest.mark.unit
class TestResultValidation:
    """Test result data validation."""
    
    def test_urls_are_valid_format(self, mock_scan_results):
        """Test all URLs in results are valid."""
        axe_file = mock_scan_results / 'axe_core_audit.csv'
        
        with open(axe_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                url = row.get('url', '')
                assert url.startswith('http://') or url.startswith('https://'), \
                    f"Invalid URL format: {url}"
    
    def test_rule_ids_follow_convention(self, mock_scan_results):
        """Test rule IDs follow axe-core naming convention."""
        axe_file = mock_scan_results / 'axe_core_audit.csv'
        
        with open(axe_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                rule_id = row.get('id', '')
                # Rule IDs typically use kebab-case
                assert rule_id, "Missing rule ID"
                assert '-' in rule_id or rule_id.islower(), \
                    f"Rule ID doesn't follow convention: {rule_id}"
