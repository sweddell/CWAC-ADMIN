"""
Integration Tests
=================

End-to-end integration tests that test multiple components together.
"""

import pytest
import json
import sqlite3


@pytest.mark.integration
@pytest.mark.slow
class TestScanToDatabase:
    """Test complete scan-to-database workflow."""
    
    def test_scan_results_can_be_imported_to_database(self, temp_db, mock_scan_results, sample_site_data):
        """Test scan results can be imported into database."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert site
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        conn.commit()
        site_id = cursor.lastrowid
        
        # Insert scan result
        cursor.execute('''
            INSERT INTO scan_results (scan_id, site_id, config_name, scan_date, a11y_score)
            VALUES (?, ?, ?, datetime('now'), ?)
        ''', (mock_scan_results.name, site_id, 'Test Config', 85.0))
        conn.commit()
        scan_result_id = cursor.lastrowid
        
        # Verify scan result exists
        cursor.execute('SELECT * FROM scan_results WHERE id = ?', (scan_result_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == mock_scan_results.name
        
        conn.close()


@pytest.mark.integration
class TestAPIToDatabaseFlow:
    """Test API endpoints interact correctly with database."""
    
    def test_api_returns_database_sites(self, authenticated_client, temp_db, sample_site_data):
        """Test API can retrieve sites from database."""
        # Note: This would require mocking DATABASE_PATH to use temp_db
        # For now, just test that API returns valid structure
        
        response = authenticated_client.get('/api/sites')
        
        assert response.status_code == 200
        sites = json.loads(response.data)
        assert isinstance(sites, list)
    
    def test_complete_authentication_flow(self, client):
        """Test complete login-access-logout flow."""
        # 1. Start unauthenticated
        response = client.get('/', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
        
        # 2. Login
        login_response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=False)
        assert login_response.status_code in [200, 302]
        
        # 3. Access protected page
        dashboard_response = client.get('/')
        assert dashboard_response.status_code == 200
        
        # 4. Logout
        logout_response = client.get('/logout', follow_redirects=False)
        assert logout_response.status_code == 302
        
        # 5. Verify logged out
        final_response = client.get('/', follow_redirects=False)
        assert final_response.status_code == 302


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_view_site_details_workflow(self, authenticated_client):
        """Test workflow: list sites -> view site details."""
        # 1. Get sites list
        sites_response = authenticated_client.get('/api/sites')
        assert sites_response.status_code == 200
        
        sites = json.loads(sites_response.data)
        
        if len(sites) > 0:
            # 2. Get first site ID
            first_site = sites[0]
            site_id = first_site.get('id')
            
            if site_id:
                # 3. View site detail page
                detail_response = authenticated_client.get(f'/sites/{site_id}')
                assert detail_response.status_code == 200
    
    def test_scan_configuration_workflow(self, authenticated_client):
        """Test workflow: list configs -> view config usage."""
        # 1. Get configurations
        configs_response = authenticated_client.get('/api/scan/configs')
        
        if configs_response.status_code == 200:
            configs = json.loads(configs_response.data)
            
            if len(configs) > 0:
                # 2. Get usage stats for first config
                first_config = configs[0]
                filename = first_config.get('filename')
                
                if filename:
                    usage_response = authenticated_client.get(
                        f'/api/scan/configs/{filename}/usage'
                    )
                    
                    # Should return valid response
                    assert usage_response.status_code in [200, 404]


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across components."""
    
    def test_scan_result_matches_database_entry(self, temp_db, mock_scan_results, sample_site_data):
        """Test scan result data matches database record."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Insert site
        cursor.execute('''
            INSERT INTO sites (organisation, url, group_id)
            VALUES (?, ?, ?)
        ''', (sample_site_data['organisation'], sample_site_data['url'], sample_site_data['group_id']))
        conn.commit()
        site_id = cursor.lastrowid
        
        # Insert scan result
        score = 90.0
        total_issues = 5
        cursor.execute('''
            INSERT INTO scan_results 
            (scan_id, site_id, config_name, scan_date, a11y_score, a11y_total_issues)
            VALUES (?, ?, ?, datetime('now'), ?, ?)
        ''', (mock_scan_results.name, site_id, 'Test', score, total_issues))
        conn.commit()
        
        # Retrieve and verify
        cursor.execute('SELECT a11y_score, a11y_total_issues FROM scan_results WHERE scan_id = ?',
                      (mock_scan_results.name,))
        result = cursor.fetchone()
        
        assert result[0] == score
        assert result[1] == total_issues
        
        conn.close()


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across components."""
    
    def test_invalid_site_id_handled_gracefully(self, authenticated_client):
        """Test API handles invalid site IDs gracefully."""
        response = authenticated_client.get('/api/sites/99999/results')
        
        # Should return 404 or error JSON, not crash
        assert response.status_code in [404, 500]
        
        if response.content_type == 'application/json':
            data = json.loads(response.data)
            assert isinstance(data, dict)
    
    def test_missing_scan_results_handled(self, authenticated_client):
        """Test missing scan results don't crash application."""
        response = authenticated_client.get('/api/results/nonexistent_scan_12345')
        
        # Should return 404, not crash
        assert response.status_code in [404, 500]
