"""
Test Database Operations
=========================

Tests for database CRUD operations and data integrity.
"""

import pytest
import sqlite3
from datetime import datetime


@pytest.mark.database
@pytest.mark.unit
class TestDatabaseSchema:
    """Test database schema and table structure."""
    
    def test_sites_table_exists(self, temp_db):
        """Test sites table exists with correct schema."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sites'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_scan_results_table_exists(self, temp_db):
        """Test scan_results table exists."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scan_results'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_page_results_table_exists(self, temp_db):
        """Test a11y_page_results table exists."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='a11y_page_results'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_issue_details_table_exists(self, temp_db):
        """Test a11y_issues table exists."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='a11y_issues'")
        assert cursor.fetchone() is not None
        
        conn.close()


@pytest.mark.database
@pytest.mark.unit
class TestSitesTable:
    """Test operations on sites table."""
    
    def test_insert_site(self, temp_db, sample_site_data):
        """Test inserting a new site."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        
        conn.commit()
        
        # Verify insertion
        cursor.execute('SELECT * FROM sites WHERE url = ?', (sample_site_data['url'],))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == sample_site_data['organisation']  # organisation
        assert result[2] == sample_site_data['url']  # url
        
        conn.close()
    
    def test_retrieve_site_by_id(self, temp_db, sample_site_data):
        """Test retrieving a site by ID."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert site
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        conn.commit()
        
        site_id = cursor.lastrowid
        
        # Retrieve by ID
        cursor.execute('SELECT * FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == site_id
        assert result[2] == sample_site_data['url']
        
        conn.close()
    
    def test_update_site(self, temp_db, sample_site_data):
        """Test updating a site record."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert site
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        conn.commit()
        site_id = cursor.lastrowid
        
        # Update organisation
        new_org = 'Updated Organization'
        cursor.execute('UPDATE sites SET organisation = ? WHERE id = ?', (new_org, site_id))
        conn.commit()
        
        # Verify update
        cursor.execute('SELECT organisation FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        
        assert result[0] == new_org
        
        conn.close()
    
    def test_delete_site(self, temp_db, sample_site_data):
        """Test deleting a site record."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert site
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        conn.commit()
        site_id = cursor.lastrowid
        
        # Delete site
        cursor.execute('DELETE FROM sites WHERE id = ?', (site_id,))
        conn.commit()
        
        # Verify deletion
        cursor.execute('SELECT * FROM sites WHERE id = ?', (site_id,))
        result = cursor.fetchone()
        
        assert result is None
        
        conn.close()
    
    def test_duplicate_url_prevented(self, temp_db, sample_site_data):
        """Test UNIQUE constraint on URL column."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert first site
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        conn.commit()
        
        # Try to insert duplicate URL
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO sites (organisation, url, group_id)
                VALUES (?, ?, ?)
            ''', ('Different Org', sample_site_data['url'], 2))
            conn.commit()
        
        conn.close()


@pytest.mark.database
@pytest.mark.unit
class TestScanResultsTable:
    """Test operations on scan_results table."""
    
    def test_insert_scan_result(self, temp_db, sample_site_data, sample_scan_data):
        """Test inserting a scan result."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert site first
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        conn.commit()
        site_id = cursor.lastrowid
        
        # Insert scan result
        sample_scan_data['site_id'] = site_id
        cursor.execute('''
            INSERT INTO scan_results 
            (scan_id, site_id, config_name, scan_date, a11y_score, a11y_total_issues, a11y_critical_issues, a11y_serious_issues)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            sample_scan_data['scan_id'],
            sample_scan_data['site_id'],
            sample_scan_data['config_name'],
            sample_scan_data['scan_date'],
            sample_scan_data['a11y_score'],
            sample_scan_data['a11y_total_issues'],
            sample_scan_data['a11y_critical_issues'],
            sample_scan_data['a11y_serious_issues']
        ))
        conn.commit()
        
        # Verify insertion
        cursor.execute('SELECT * FROM scan_results WHERE scan_id = ?', (sample_scan_data['scan_id'],))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == sample_scan_data['scan_id']  # scan_id
        assert result[5] == sample_scan_data['a11y_score']  # a11y_score
        
        conn.close()
    
    def test_foreign_key_constraint(self, temp_db, sample_scan_data):
        """Test foreign key constraint on site_id."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Try to insert scan result with non-existent site_id
        # Note: SQLite foreign keys must be enabled
        cursor.execute('PRAGMA foreign_keys = ON')
        
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO scan_results 
                (scan_id, site_id, config_name, scan_date, a11y_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (sample_scan_data['scan_id'], 99999, 'Test', datetime.now().isoformat(), 85.0))
            conn.commit()
        
        conn.close()


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseQueries:
    """Test complex database queries."""
    
    def test_get_latest_scan_for_site(self, temp_db, sample_site_data, sample_scan_data):
        """Test retrieving the most recent scan for a site."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert site
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        conn.commit()
        site_id = cursor.lastrowid
        
        # Insert multiple scan results
        for i in range(3):
            scan_id = f'scan_{i}_{datetime.now().isoformat()}'
            cursor.execute('''
                INSERT INTO scan_results (scan_id, site_id, config_name, scan_date, a11y_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (scan_id, site_id, 'Config', datetime.now().isoformat(), 80.0 + i))
            conn.commit()
        
        # Get latest scan
        cursor.execute('''
            SELECT * FROM scan_results 
            WHERE site_id = ? 
            ORDER BY scan_date DESC 
            LIMIT 1
        ''', (site_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[5] == 82.0  # Latest score (80 + 2)
        
        conn.close()
    
    def test_count_total_issues_across_sites(self, temp_db, sample_site_data, sample_scan_data):
        """Test aggregating issues across all sites."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert sites and scans
        for i in range(3):
            cursor.execute('''
                INSERT INTO sites (organisation, url, group_id)
                VALUES (?, ?, ?)
            ''', (f'Org {i}', f'https://example{i}.com', 1))
            conn.commit()
            site_id = cursor.lastrowid
            
            cursor.execute('''
                INSERT INTO scan_results (scan_id, site_id, config_name, scan_date, a11y_total_issues)
                VALUES (?, ?, ?, ?, ?)
            ''', (f'scan_{i}', site_id, 'Config', datetime.now().isoformat(), 10 * (i + 1)))
            conn.commit()
        
        # Count total issues
        cursor.execute('SELECT SUM(a11y_total_issues) FROM scan_results')
        total = cursor.fetchone()[0]
        
        assert total == 60  # 10 + 20 + 30
        
        conn.close()
