"""
Test Jinja UI Route and Static Assets
=====================================
Tests for:
  - GET / (HTML template rendering)
  - GET /static/css/style.css
  - GET /static/js/app.js
  - HTML structure, accessibility, and security checks
Phase 9 Implementation.
"""

from fastapi.testclient import TestClient
from app.main import app


def test_ui_route_returns_html_and_title():
    """GET / renders index.html with 200 OK and expected banking title."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        html = response.text
        assert "NovaBank AI" in html
        assert "Banking Customer Assistant" in html
        assert "<!DOCTYPE html>" in html


def test_ui_route_contains_required_chat_elements():
    """HTML contains all required functional elements from spec Section 7."""
    with TestClient(app) as client:
        response = client.get("/")
        html = response.text

        # Customer ID input & new chat button
        assert 'id="customer-id-input"' in html
        assert 'id="new-chat-btn"' in html

        # Chat display area & active conversation badge
        assert 'id="messages-container"' in html
        assert 'id="active-conv-id"' in html

        # Message input & send button
        assert 'id="message-input"' in html
        assert 'id="send-btn"' in html

        # Loading & error indicators
        assert 'id="loading-indicator"' in html
        assert 'id="error-banner"' in html
        assert 'id="system-status"' in html


def test_ui_route_references_static_assets():
    """HTML references the stylesheet and javascript application files."""
    with TestClient(app) as client:
        response = client.get("/")
        html = response.text

        assert 'href="/static/css/style.css"' in html
        assert 'src="/static/js/app.js"' in html


def test_static_css_accessible():
    """GET /static/css/style.css returns 200 and CSS stylesheet content."""
    with TestClient(app) as client:
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
        assert "--primary-navy" in response.text


def test_static_js_accessible():
    """GET /static/js/app.js returns 200 and JavaScript content."""
    with TestClient(app) as client:
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert any(
            t in response.headers["content-type"]
            for t in ["application/javascript", "text/javascript"]
        )
        assert "NovaBank AI Banking Customer Assistant" in response.text
        assert "/api/chat" in response.text


def test_ui_security_no_secrets_in_html():
    """Verify that no database paths, API keys, or internal tokens appear in HTML."""
    with TestClient(app) as client:
        response = client.get("/")
        html = response.text

        assert "conversations.db" not in html
        assert "sk-" not in html
        assert "api_key" not in html.lower()
        assert "password" not in html.lower()
