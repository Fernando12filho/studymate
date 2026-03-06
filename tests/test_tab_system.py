"""
Tests for the VS Code-like Tab System.

Feature: When a user clicks a document (note or resource) in the left panel,
         it opens in a tab in the main content area.  Multiple tabs can be open
         simultaneously; tabs can be closed; the active tab is highlighted.

The tab system itself is a **front-end** feature, but it relies on these
back-end API endpoints to load document content into each tab:

  GET /api/notes/<int:note_id>         – Note content (for "note" tabs)
  GET /api/resources/<int:resource_id> – Resource metadata + content (for "resource" tabs)

Secondary endpoint (optional, for persisting tab state across reloads):
  GET  /api/tab-state                  – Retrieve the user's saved open-tab list
  POST /api/tab-state                  – Persist the user's open-tab list

Each content endpoint must:
  - Require authentication
  - Return only the requesting user's own documents (403 / 404 for others)
  - Return JSON with enough data for the tab to render the document

These tests will FAIL until the endpoints are implemented.
"""

import json
import pytest


# ---------------------------------------------------------------------------
# Note-tab content endpoint   GET /api/notes/<id>
# ---------------------------------------------------------------------------

class TestNoteTabContent:
    """GET /api/notes/<int:note_id>"""

    def test_requires_authentication(self, client, test_note):
        response = client.get(f"/api/notes/{test_note.id}")
        assert response.status_code in (401, 302)

    def test_returns_note_when_owner(self, logged_in_client, test_note):
        response = logged_in_client.get(f"/api/notes/{test_note.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == test_note.id

    def test_note_content_schema(self, logged_in_client, test_note):
        """Note tab payload must include all fields needed to render the tab."""
        response = logged_in_client.get(f"/api/notes/{test_note.id}")
        assert response.status_code == 200
        data = json.loads(response.data)

        required_fields = {
            "id", "title", "content", "content_html",
            "topic_id", "topic_name",
            "is_ai_generated", "created_at", "updated_at",
        }
        missing = required_fields - set(data.keys())
        assert not missing, f"Note tab payload is missing fields: {missing}"

    def test_content_html_is_rendered_markdown(self, logged_in_client, test_note):
        """content_html should be Markdown rendered to HTML."""
        response = logged_in_client.get(f"/api/notes/{test_note.id}")
        data = json.loads(response.data)
        # The test note content starts with '# Heading' – expect an <h1> tag
        assert "<h1>" in data["content_html"] or "<h" in data["content_html"], (
            "content_html must contain rendered Markdown (at least one heading tag)"
        )

    def test_returns_404_for_nonexistent_note(self, logged_in_client):
        response = logged_in_client.get("/api/notes/999999")
        assert response.status_code == 404

    def test_returns_403_for_another_users_note(
        self, logged_in_client, other_user, db, app, test_topic
    ):
        """A user must not be able to read another user's note via the tab API."""
        from app.models import Note

        with app.app_context():
            other_topic = _make_topic(db, other_user.id)
            private_note = Note(
                title="Private",
                content="Secret",
                is_ai_generated=False,
                user_id=other_user.id,
                topic_id=other_topic.id,
            )
            db.session.add(private_note)
            db.session.commit()
            private_id = private_note.id

        response = logged_in_client.get(f"/api/notes/{private_id}")
        assert response.status_code in (403, 404), (
            "Should not expose another user's note"
        )


# ---------------------------------------------------------------------------
# Resource-tab content endpoint   GET /api/resources/<id>
# ---------------------------------------------------------------------------

class TestResourceTabContent:
    """GET /api/resources/<int:resource_id>"""

    def test_requires_authentication(self, client, test_resource_link):
        response = client.get(f"/api/resources/{test_resource_link.id}")
        assert response.status_code in (401, 302)

    def test_returns_resource_when_owner(self, logged_in_client, test_resource_link):
        response = logged_in_client.get(f"/api/resources/{test_resource_link.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == test_resource_link.id

    def test_link_resource_schema(self, logged_in_client, test_resource_link):
        response = logged_in_client.get(f"/api/resources/{test_resource_link.id}")
        data = json.loads(response.data)

        required_fields = {
            "id", "title", "resource_type", "url",
            "topic_id", "topic_name", "created_at",
        }
        missing = required_fields - set(data.keys())
        assert not missing, f"Link resource tab payload missing: {missing}"

    def test_pdf_resource_schema(self, logged_in_client, test_resource_pdf):
        response = logged_in_client.get(f"/api/resources/{test_resource_pdf.id}")
        assert response.status_code == 200
        data = json.loads(response.data)

        required_fields = {
            "id", "title", "resource_type",
            "original_filename", "file_size",
            "topic_id", "topic_name",
        }
        missing = required_fields - set(data.keys())
        assert not missing, f"PDF resource tab payload missing: {missing}"

    def test_pdf_resource_includes_viewer_url(self, logged_in_client, test_resource_pdf):
        """PDF resources must expose a URL the browser can load in an <iframe>."""
        response = logged_in_client.get(f"/api/resources/{test_resource_pdf.id}")
        data = json.loads(response.data)
        assert "viewer_url" in data or "file_url" in data, (
            "PDF resource must include viewer_url or file_url"
        )

    def test_returns_404_for_nonexistent_resource(self, logged_in_client):
        response = logged_in_client.get("/api/resources/999999")
        assert response.status_code == 404

    def test_returns_403_for_another_users_resource(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Resource

        with app.app_context():
            other_topic = _make_topic(db, other_user.id)
            private_res = Resource(
                title="Private Resource",
                resource_type="link",
                url="https://private.example.com",
                user_id=other_user.id,
                topic_id=other_topic.id,
            )
            db.session.add(private_res)
            db.session.commit()
            private_id = private_res.id

        response = logged_in_client.get(f"/api/resources/{private_id}")
        assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Tab-state persistence API   GET/POST /api/tab-state
# ---------------------------------------------------------------------------

class TestTabStatePersistence:
    """
    Optional: persist which tabs are open so that a page refresh restores them.

    POST /api/tab-state  body: {"tabs": [{"type": "note", "id": 1}, ...]}
    GET  /api/tab-state  returns: {"tabs": [...]}
    """

    def test_save_tab_state_requires_authentication(self, client):
        response = client.post(
            "/api/tab-state",
            data=json.dumps({"tabs": []}),
            content_type="application/json",
        )
        assert response.status_code in (401, 302)

    def test_save_and_retrieve_tab_state(self, logged_in_client):
        tabs = [
            {"type": "note", "id": 1},
            {"type": "resource", "id": 2},
        ]
        post_resp = logged_in_client.post(
            "/api/tab-state",
            data=json.dumps({"tabs": tabs}),
            content_type="application/json",
        )
        assert post_resp.status_code in (200, 201)

        get_resp = logged_in_client.get("/api/tab-state")
        assert get_resp.status_code == 200
        data = json.loads(get_resp.data)
        assert "tabs" in data
        assert data["tabs"] == tabs

    def test_saving_empty_tabs_clears_state(self, logged_in_client):
        # First save something
        logged_in_client.post(
            "/api/tab-state",
            data=json.dumps({"tabs": [{"type": "note", "id": 1}]}),
            content_type="application/json",
        )
        # Then clear
        logged_in_client.post(
            "/api/tab-state",
            data=json.dumps({"tabs": []}),
            content_type="application/json",
        )
        get_resp = logged_in_client.get("/api/tab-state")
        data = json.loads(get_resp.data)
        assert data["tabs"] == []

    def test_tab_state_is_user_specific(
        self, app, client, test_user, other_user
    ):
        """Two different users must have independent tab states."""
        # Log in as test_user and save tabs
        with app.app_context():
            with client.session_transaction() as sess:
                sess["_user_id"] = str(test_user.id)
                sess["_fresh"] = True

        client.post(
            "/api/tab-state",
            data=json.dumps({"tabs": [{"type": "note", "id": 42}]}),
            content_type="application/json",
        )

        # Switch to other_user
        with app.app_context():
            with client.session_transaction() as sess:
                sess["_user_id"] = str(other_user.id)
                sess["_fresh"] = True

        get_resp = client.get("/api/tab-state")
        data = json.loads(get_resp.data)
        # other_user should have an empty tab list, not test_user's
        assert data["tabs"] != [{"type": "note", "id": 42}]


# ---------------------------------------------------------------------------
# Dashboard renders with tab chrome
# ---------------------------------------------------------------------------

class TestDashboardTabHtml:
    """The dashboard HTML must include the tab container elements."""

    def test_dashboard_has_tab_bar_element(self, logged_in_client):
        response = logged_in_client.get("/dashboard")
        assert response.status_code == 200
        html = response.data.decode()
        assert 'id="tabBar"' in html or 'class="tab-bar"' in html, (
            "Dashboard must include a #tabBar or .tab-bar element"
        )

    def test_dashboard_has_tab_content_area(self, logged_in_client):
        response = logged_in_client.get("/dashboard")
        html = response.data.decode()
        assert 'id="tabContent"' in html or 'class="tab-content"' in html, (
            "Dashboard must include a #tabContent or .tab-content element"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_topic(db, user_id: int):
    from app.models import Topic

    topic = Topic(name="Temp Topic", user_id=user_id)
    db.session.add(topic)
    db.session.commit()
    return topic
