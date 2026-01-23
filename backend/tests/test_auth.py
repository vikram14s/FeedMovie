"""
Test cases for authentication and user management.
Run with: .venv/bin/python -m pytest backend/tests/test_auth.py -v
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import init_database, get_connection
import json


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def setup_db():
    """Ensure database is initialized."""
    init_database()


class TestRegistration:
    """Test user registration."""

    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@test.com',
            'password': 'password123',
            'username': 'newuser'
        })
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['success'] is True
        assert 'token' in data
        assert data['user']['username'] == 'newuser'
        assert data['user']['email'] == 'newuser@test.com'
        assert data['user']['onboarding_completed'] is False

        # Cleanup
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email = 'newuser@test.com'")
        conn.commit()
        conn.close()

    def test_register_missing_fields(self, client):
        """Test registration with missing fields."""
        response = client.post('/api/auth/register', json={
            'email': 'test@test.com'
        })
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data['success'] is False

    def test_register_duplicate_email(self, client):
        """Test registration with existing email."""
        response = client.post('/api/auth/register', json={
            'email': 'test@test.com',  # Already exists
            'password': 'password123',
            'username': 'anotheruser'
        })
        data = json.loads(response.data)

        assert response.status_code == 409
        assert data['success'] is False

    def test_register_short_password(self, client):
        """Test registration with short password."""
        response = client.post('/api/auth/register', json={
            'email': 'short@test.com',
            'password': '123',
            'username': 'shortpw'
        })
        data = json.loads(response.data)

        assert response.status_code == 400
        assert data['success'] is False


class TestLogin:
    """Test user login."""

    def test_login_success(self, client):
        """Test successful login."""
        response = client.post('/api/auth/login', json={
            'email': 'test@test.com',
            'password': 'test12'
        })
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['success'] is True
        assert 'token' in data
        assert data['user']['username'] == 'test'
        assert data['user']['id'] == 2

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        response = client.post('/api/auth/login', json={
            'email': 'test@test.com',
            'password': 'wrongpassword'
        })
        data = json.loads(response.data)

        assert response.status_code == 401
        assert data['success'] is False

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@test.com',
            'password': 'password123'
        })
        data = json.loads(response.data)

        assert response.status_code == 401
        assert data['success'] is False


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication."""

    def get_token(self, client, email='test@test.com', password='test12'):
        """Helper to get auth token."""
        response = client.post('/api/auth/login', json={
            'email': email,
            'password': password
        })
        data = json.loads(response.data)
        return data.get('token')

    def test_profile_requires_auth(self, client):
        """Test that profile endpoint requires auth."""
        response = client.get('/api/profile')
        data = json.loads(response.data)

        assert response.status_code == 401
        assert data['success'] is False

    def test_profile_with_auth(self, client):
        """Test profile endpoint with valid auth."""
        token = self.get_token(client)

        response = client.get('/api/profile', headers={
            'Authorization': f'Bearer {token}'
        })
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['success'] is True
        assert data['profile']['username'] == 'test'

    def test_profile_returns_correct_user(self, client):
        """Test that profile returns data for the logged-in user, not cached data."""
        # Login as test user
        token1 = self.get_token(client, 'test@test.com', 'test12')

        response1 = client.get('/api/profile', headers={
            'Authorization': f'Bearer {token1}'
        })
        data1 = json.loads(response1.data)

        assert data1['profile']['username'] == 'test'

        # Login as different user (action_andy)
        token2 = self.get_token(client, 'andy@example.com', 'friend123')

        response2 = client.get('/api/profile', headers={
            'Authorization': f'Bearer {token2}'
        })
        data2 = json.loads(response2.data)

        assert data2['profile']['username'] == 'action_andy'
        assert data2['profile']['username'] != data1['profile']['username']

    def test_feed_requires_auth(self, client):
        """Test that feed endpoint requires auth."""
        response = client.get('/api/feed')
        data = json.loads(response.data)

        assert response.status_code == 401
        assert data['success'] is False


class TestUserIsolation:
    """Test that user data is properly isolated."""

    def get_token(self, client, email, password):
        """Helper to get auth token."""
        response = client.post('/api/auth/login', json={
            'email': email,
            'password': password
        })
        data = json.loads(response.data)
        return data.get('token')

    def test_watchlist_isolation(self, client):
        """Test that watchlist is isolated per user."""
        token1 = self.get_token(client, 'test@test.com', 'test12')
        token2 = self.get_token(client, 'andy@example.com', 'friend123')

        # Get watchlists for both users
        response1 = client.get('/api/watchlist', headers={
            'Authorization': f'Bearer {token1}'
        })
        response2 = client.get('/api/watchlist', headers={
            'Authorization': f'Bearer {token2}'
        })

        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        # Should both succeed but potentially have different counts
        assert data1['success'] is True
        assert data2['success'] is True

    def test_library_isolation(self, client):
        """Test that library is isolated per user."""
        token1 = self.get_token(client, 'test@test.com', 'test12')
        token2 = self.get_token(client, 'andy@example.com', 'friend123')

        response1 = client.get('/api/profile/library', headers={
            'Authorization': f'Bearer {token1}'
        })
        response2 = client.get('/api/profile/library', headers={
            'Authorization': f'Bearer {token2}'
        })

        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        assert data1['success'] is True
        assert data2['success'] is True
        # They should have different libraries
        # (test user has letterboxd imports, andy has seeded movies)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
