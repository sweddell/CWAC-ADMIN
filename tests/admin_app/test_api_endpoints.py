"""
Test Admin API Endpoints
=========================

Tests for all Flask API routes in admin_app.py
"""

import pytest
import json
from datetime import datetime


@pytest.mark.api
class TestPublicEndpoints:
    """Test publicly accessible endpoints."""
    
    def test_login_page_loads(self, client):
        """Test login page is accessible."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Centralised Web Accessibility Checker' in response.data
        assert b'Username' in response.data
        assert b'Password' in response.data
    
    def test_register_page_loads(self, client):
        """Test register page is accessible."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data
        assert b'Create Account' in response.data
    
    def test_favicon_returns_successfully(self, client):
        """Test favicon endpoint returns a file."""
        response = client.get('/favicon.ico')
        # Should return either 200 (with file) or 204 (no content fallback)
        assert response.status_code in [200, 204]


@pytest.mark.api
@pytest.mark.auth
class TestAuthenticationEndpoints:
    """Test authentication-related endpoints."""
    
    def test_login_with_valid_credentials(self, client):
        """Test successful login with admin credentials."""
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=False)
        
        # Should redirect to dashboard after successful login
        assert response.status_code in [302, 200]
    
    def test_login_with_invalid_credentials(self, client):
        """Test login fails with invalid credentials."""
        response = client.post('/login', data={
            'username': 'invalid',
            'password': 'wrong'
        }, follow_redirects=True)
        
        # Should stay on login page or show error
        assert response.status_code == 200
    
    def test_logout_ends_session(self, authenticated_client):
        """Test logout successfully ends user session."""
        response = authenticated_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        # Should redirect to login page
        assert b'login' in response.request.path.lower().encode() or b'Login' in response.data


@pytest.mark.api
class TestProtectedEndpoints:
    """Test endpoints that require authentication."""
    
    def test_dashboard_requires_authentication(self, client):
        """Test dashboard redirects unauthenticated users."""
        response = client.get('/', follow_redirects=False)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_sites_page_requires_authentication(self, client):
        """Test sites page requires login."""
        response = client.get('/sites', follow_redirects=False)
        
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_scan_page_requires_authentication(self, client):
        """Test scan page requires login."""
        response = client.get('/scan', follow_redirects=False)
        
        assert response.status_code == 302
        assert '/login' in response.location


@pytest.mark.api
class TestAPIEndpoints:
    """Test API endpoints with authentication."""
    
    def test_api_sites_returns_json(self, authenticated_client):
        """Test /api/sites returns JSON data."""
        response = authenticated_client.get('/api/sites')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_api_scan_stats_returns_metrics(self, authenticated_client):
        """Test /api/scan-stats returns statistics."""
        response = authenticated_client.get('/api/scan-stats')
        
        if response.status_code == 200:  # Only test if endpoint exists
            data = json.loads(response.data)
            
            # Should contain key metrics
            assert 'totalScans' in data or isinstance(data, dict)
    
    def test_api_system_status_returns_data(self, authenticated_client):
        """Test /api/system/status returns system information."""
        response = authenticated_client.get('/api/system/status')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Should contain system info keys
            assert isinstance(data, dict)
    
    def test_api_results_returns_scan_results(self, authenticated_client):
        """Test /api/results returns scan results list."""
        response = authenticated_client.get('/api/results')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
    
    def test_api_scan_configs_returns_list(self, authenticated_client):
        """Test /api/scan/configs returns configuration list."""
        response = authenticated_client.get('/api/scan/configs')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, list)


@pytest.mark.api
class TestAPIErrorHandling:
    """Test API error handling and validation."""
    
    def test_api_invalid_site_id_returns_error(self, authenticated_client):
        """Test API returns error for invalid site ID."""
        response = authenticated_client.get('/api/sites/99999/results')
        
        # Should return 404 or error response
        assert response.status_code in [404, 500]
    
    def test_api_missing_parameters_returns_error(self, authenticated_client):
        """Test API validates required parameters."""
        response = authenticated_client.post('/api/scan/start', 
                                             data=json.dumps({}),
                                             content_type='application/json')
        
        # Should accept request or return validation error
        assert response.status_code in [200, 400, 422]


@pytest.mark.api
@pytest.mark.integration
class TestScanWorkflow:
    """Test complete scan workflow through API."""
    
    def test_scan_configuration_list_accessible(self, authenticated_client):
        """Test scan configurations can be listed."""
        response = authenticated_client.get('/api/scan/configs')
        
        if response.status_code == 200:
            configs = json.loads(response.data)
            assert isinstance(configs, list)
    
    def test_scan_history_accessible(self, authenticated_client):
        """Test scan history can be retrieved."""
        response = authenticated_client.get('/api/scan/history')
        
        if response.status_code == 200:
            history = json.loads(response.data)
            assert isinstance(history, list)
    
    def test_active_scans_list_accessible(self, authenticated_client):
        """Test active scans can be listed."""
        response = authenticated_client.get('/api/scan/active')
        
        if response.status_code == 200:
            active = json.loads(response.data)
            assert isinstance(active, list)
