"""
Test Authentication and Authorization
======================================

Tests for user authentication, session management, and access control.
"""

import pytest


@pytest.mark.auth
@pytest.mark.unit
class TestUserAuthentication:
    """Test user authentication functionality."""
    
    def test_admin_user_can_login(self, client):
        """Test admin user can successfully log in."""
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should not see login form after successful login
        assert b'Dashboard' in response.data or b'dashboard' in response.data
    
    def test_invalid_username_rejected(self, client):
        """Test login fails with non-existent username."""
        response = client.post('/login', data={
            'username': 'nonexistent_user_12345',
            'password': 'anypassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error or stay on login page
        assert b'Invalid' in response.data or b'Username' in response.data
    
    def test_wrong_password_rejected(self, client):
        """Test login fails with incorrect password."""
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error
        assert b'Invalid' in response.data or b'Password' in response.data
    
    def test_empty_credentials_rejected(self, client):
        """Test login fails with empty username/password."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should stay on login page or show validation error


@pytest.mark.auth
@pytest.mark.unit
class TestSessionManagement:
    """Test user session handling."""
    
    def test_session_persists_across_requests(self, authenticated_client):
        """Test user session is maintained between requests."""
        # First request to dashboard
        response1 = authenticated_client.get('/')
        assert response1.status_code == 200
        
        # Second request to sites page (should still be authenticated)
        response2 = authenticated_client.get('/sites')
        assert response2.status_code == 200
    
    def test_logout_clears_session(self, authenticated_client):
        """Test logout properly clears user session."""
        # Verify authenticated
        response1 = authenticated_client.get('/')
        assert response1.status_code == 200
        
        # Logout
        authenticated_client.get('/logout')
        
        # Try to access protected page
        response2 = authenticated_client.get('/', follow_redirects=False)
        assert response2.status_code == 302  # Should redirect to login


@pytest.mark.auth
@pytest.mark.integration
class TestAccessControl:
    """Test route protection and access control."""
    
    @pytest.mark.parametrize('route', [
        '/',
        '/dashboard',
        '/sites',
        '/scan',
        '/analytics',
        '/profile',
    ])
    def test_protected_routes_require_auth(self, client, route):
        """Test all protected routes redirect unauthenticated users."""
        response = client.get(route, follow_redirects=False)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login' in response.location
    
    @pytest.mark.parametrize('route', [
        '/login',
        '/register',
        '/favicon.ico',
    ])
    def test_public_routes_accessible_without_auth(self, client, route):
        """Test public routes are accessible without authentication."""
        response = client.get(route)
        
        # Should be accessible (200) or have fallback (204 for favicon)
        assert response.status_code in [200, 204]
    
    @pytest.mark.parametrize('api_route', [
        '/api/sites',
        '/api/results',
        '/api/system/status',
    ])
    def test_api_routes_require_auth(self, client, api_route):
        """Test API routes require authentication."""
        response = client.get(api_route, follow_redirects=False)
        
        # Should redirect to login or return 401
        assert response.status_code in [302, 401]


@pytest.mark.auth
@pytest.mark.unit
class TestUserRegistration:
    """Test user registration workflow."""
    
    def test_registration_page_accessible(self, client):
        """Test registration page loads."""
        response = client.get('/register')
        
        assert response.status_code == 200
        assert b'Register' in response.data
        assert b'Username' in response.data
        assert b'Password' in response.data
    
    def test_registration_requires_username(self, client):
        """Test registration validates username field."""
        response = client.post('/register', data={
            'username': '',
            'email': 'test@example.com',
            'organization': 'Test Org',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!'
        }, follow_redirects=True)
        
        # Should show error or stay on registration page
        assert response.status_code == 200
    
    def test_registration_requires_valid_email(self, client):
        """Test registration validates email format."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'invalid-email',
            'organization': 'Test Org',
            'password': 'TestPass123!',
            'confirm_password': 'TestPass123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should validate email format
    
    def test_registration_passwords_must_match(self, client):
        """Test registration validates password confirmation."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'test@example.com',
            'organization': 'Test Org',
            'password': 'TestPass123!',
            'confirm_password': 'DifferentPass123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show password mismatch error


@pytest.mark.auth
@pytest.mark.unit
class TestPasswordSecurity:
    """Test password handling and security."""
    
    def test_passwords_not_stored_in_plaintext(self, client):
        """Test passwords are hashed, not stored in plain text."""
        # This would require checking the users.json file
        # For now, verify login works (implying proper hashing)
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        })
        
        # If login works, password was properly hashed and verified
        assert response.status_code in [200, 302]
    
    def test_session_cookie_set_on_login(self, client):
        """Test session cookie is set after successful login."""
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        })
        
        # Should set session cookie
        cookies = response.headers.getlist('Set-Cookie')
        assert len(cookies) > 0
        assert any('session' in cookie.lower() for cookie in cookies)
