"""
Pytest Configuration and Shared Fixtures
=========================================

This file contains fixtures that are available to all tests.
"""

import pytest
import sys
import os
import tempfile
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

# Add application paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'cwac_admin_app' / 'app'))
sys.path.insert(0, str(PROJECT_ROOT / 'cwac'))


@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask test application."""
    from admin_app import app as flask_app
    
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
    })
    
    yield flask_app


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def authenticated_client(client):
    """Create an authenticated test client."""
    # Login with default admin credentials
    client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    
    yield client
    
    # Logout after test
    client.get('/logout', follow_redirects=True)


@pytest.fixture(scope='function')
def temp_db():
    """Create a temporary test database."""
    # Create temp directory and database
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / 'test_cwac_analytics.db'
    
    # Create database with schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create sites table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organisation TEXT,
            url TEXT UNIQUE NOT NULL,
            group_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create scan_results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT UNIQUE NOT NULL,
            site_id INTEGER,
            config_name TEXT,
            scan_date TIMESTAMP,
            a11y_score REAL,
            a11y_total_issues INTEGER,
            a11y_critical_issues INTEGER,
            a11y_serious_issues INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites (id)
        )
    ''')
    
    # Create a11y_page_results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS a11y_page_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_result_id INTEGER,
            page_url TEXT,
            page_title TEXT,
            critical_count INTEGER,
            serious_count INTEGER,
            moderate_count INTEGER,
            minor_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scan_result_id) REFERENCES scan_results (id)
        )
    ''')
    
    # Create a11y_issues table (matching actual schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS a11y_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_result_id INTEGER,
            page_url TEXT,
            issue_id TEXT,
            impact TEXT,
            description TEXT,
            help TEXT,
            help_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scan_result_id) REFERENCES scan_results (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    yield str(db_path)
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(scope='function')
def sample_site_data():
    """Provide sample site data for testing."""
    return {
        'organisation': 'Test Organization',
        'url': 'https://example.com',
        'group_id': 1
    }


@pytest.fixture(scope='function')
def sample_scan_data():
    """Provide sample scan result data for testing."""
    return {
        'scan_id': 'test_scan_2025-01-01_12-00-00',
        'site_id': 1,
        'config_name': 'Test Config',
        'scan_date': datetime.now().isoformat(),
        'a11y_score': 85.5,
        'a11y_total_issues': 10,
        'a11y_critical_issues': 2,
        'a11y_serious_issues': 3
    }


@pytest.fixture(scope='function')
def sample_config():
    """Provide sample scan configuration for testing."""
    return {
        'audit_name': 'Test Audit',
        'headless': True,
        'max_links_per_domain': 5,
        'thread_count': 2,
        'browser': 'chrome',
        'viewport_sizes': {
            'small': {'width': 320, 'height': 568},
            'medium': {'width': 1366, 'height': 768}
        }
    }


@pytest.fixture(scope='function')
def mock_scan_results(tmp_path):
    """Create mock scan result files."""
    result_dir = tmp_path / 'test_scan_results'
    result_dir.mkdir()
    
    # Create .scan_success marker
    (result_dir / '.scan_success').touch()
    
    # Create sample CSV files
    axe_csv = result_dir / 'axe_core_audit.csv'
    axe_csv.write_text(
        'url,page_title,id,impact,description,help,helpUrl,target\n'
        'https://example.com,Example,color-contrast,serious,Color contrast,Improve contrast,https://help.com,body\n'
        'https://example.com,Example,image-alt,critical,Missing alt,Add alt text,https://help.com,img\n'
    )
    
    pages_csv = result_dir / 'pages_scanned.csv'
    pages_csv.write_text(
        'url,page_title,status\n'
        'https://example.com,Example,success\n'
    )
    
    return result_dir


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test."""
    # Set test environment
    monkeypatch.setenv('FLASK_ENV', 'testing')
    monkeypatch.setenv('TESTING', 'true')
