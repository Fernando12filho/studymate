"""
Tests for the Left Panel Document Listing API.

Feature: All resources and notes are listed in the left panel of the dashboard.

API endpoints to be implemented:
  GET /api/notes               – List notes for the current user (optionally filtered by topic)
  GET /api/resources           – List resources for the current user (optionally filtered by topic)
  GET /api/documents           – Combined list (notes + resources) with a `type` field

Each endpoint must:
  - Require authentication (401 when not logged in)
  - Return only documents owned by the current user
  - Support optional `?topic_id=<int>` query parameter
  - Return JSON with a predictable schema

These tests will FAIL until the endpoints are implemented.
"""

import json
import pytest


class TestNotesListEndpoint:
    """GET /api/notes"""

    def test_requires_authentication(self, client):
        """Unauthenticated request should be redirected or return 401."""
        response = client.get("/api/notes")
        assert response.status_code in (401, 302), (
            "Expected 401 Unauthorized or 302 redirect for unauthenticated request"
        )

    def test_returns_ok_when_authenticated(self, logged_in_client):
        """Authenticated request returns 200 with JSON."""
        response = logged_in_client.get("/api/notes")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "notes" in data, "Response JSON must contain a 'notes' key"

    def test_returns_only_current_user_notes(self, logged_in_client, test_note, other_user, db, app, test_topic):
        """User should only see their own notes, not another user's notes."""
        from app.models import Note

        # Create a note owned by other_user in the same topic would need another topic,
        # but we just check the returned ids contain only test_user's note.
        with app.app_context():
            other_topic = _make_topic(db, other_user.id)
            other_note = Note(
                title="Other User Note",
                content="Private content",
                is_ai_generated=False,
                user_id=other_user.id,
                topic_id=other_topic.id,
            )
            db.session.add(other_note)
            db.session.commit()
            other_note_id = other_note.id

        response = logged_in_client.get("/api/notes")
        assert response.status_code == 200
        data = json.loads(response.data)
        returned_ids = [n["id"] for n in data["notes"]]
        assert other_note_id not in returned_ids, (
            "Other user's note must not appear in the current user's list"
        )

    def test_empty_list_when_no_notes(self, logged_in_client):
        """Returns an empty list (not a 404) when the user has no notes."""
        response = logged_in_client.get("/api/notes")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data["notes"], list)

    def test_note_schema(self, logged_in_client, test_note):
        """Each note item contains all required fields for the left panel."""
        response = logged_in_client.get("/api/notes")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert len(data["notes"]) >= 1
        note = next(n for n in data["notes"] if n["id"] == test_note.id)

        required_fields = {"id", "title", "topic_id", "topic_name", "created_at", "is_ai_generated", "type"}
        missing = required_fields - set(note.keys())
        assert not missing, f"Note item is missing fields: {missing}"
        assert note["type"] == "note"

    def test_filter_by_topic_id(self, logged_in_client, test_note, test_topic, db, app, test_user):
        """?topic_id=<id> filters notes to only that topic."""
        from app.models import Topic, Note

        # Create a second topic + note that should NOT appear
        with app.app_context():
            topic2 = Topic(name="Other Topic", user_id=test_user.id)
            db.session.add(topic2)
            db.session.commit()
            note2 = Note(
                title="Note in Topic 2",
                content="...",
                is_ai_generated=False,
                user_id=test_user.id,
                topic_id=topic2.id,
            )
            db.session.add(note2)
            db.session.commit()
            topic2_id = topic2.id

        response = logged_in_client.get(f"/api/notes?topic_id={test_topic.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        for note in data["notes"]:
            assert note["topic_id"] == test_topic.id, (
                f"Note with topic_id={note['topic_id']} should not appear when "
                f"filtering by topic_id={test_topic.id}"
            )

    def test_includes_ai_generated_notes(self, logged_in_client, ai_note):
        """AI-generated notes must also appear in the list."""
        response = logged_in_client.get("/api/notes")
        assert response.status_code == 200
        data = json.loads(response.data)
        ai_note_ids = [n["id"] for n in data["notes"] if n.get("is_ai_generated")]
        assert ai_note.id in ai_note_ids, "AI-generated note must appear in the notes list"


class TestResourcesListEndpoint:
    """GET /api/resources"""

    def test_requires_authentication(self, client):
        response = client.get("/api/resources")
        assert response.status_code in (401, 302)

    def test_returns_ok_when_authenticated(self, logged_in_client):
        response = logged_in_client.get("/api/resources")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "resources" in data

    def test_returns_only_current_user_resources(
        self, logged_in_client, test_resource_link, other_user, db, app
    ):
        from app.models import Resource

        with app.app_context():
            other_topic = _make_topic(db, other_user.id)
            other_res = Resource(
                title="Other user's resource",
                resource_type="link",
                url="https://other.example.com",
                user_id=other_user.id,
                topic_id=other_topic.id,
            )
            db.session.add(other_res)
            db.session.commit()
            other_res_id = other_res.id

        response = logged_in_client.get("/api/resources")
        data = json.loads(response.data)
        returned_ids = [r["id"] for r in data["resources"]]
        assert other_res_id not in returned_ids

    def test_resource_schema(self, logged_in_client, test_resource_link):
        """Each resource item contains all required fields for the left panel."""
        response = logged_in_client.get("/api/resources")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert len(data["resources"]) >= 1
        resource = next(r for r in data["resources"] if r["id"] == test_resource_link.id)

        required_fields = {"id", "title", "resource_type", "topic_id", "topic_name", "created_at", "type"}
        missing = required_fields - set(resource.keys())
        assert not missing, f"Resource item is missing fields: {missing}"
        assert resource["type"] == "resource"

    def test_filter_by_topic_id(self, logged_in_client, test_resource_link, test_topic):
        response = logged_in_client.get(f"/api/resources?topic_id={test_topic.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        for r in data["resources"]:
            assert r["topic_id"] == test_topic.id

    def test_link_resource_has_url(self, logged_in_client, test_resource_link):
        response = logged_in_client.get("/api/resources")
        data = json.loads(response.data)
        res = next(r for r in data["resources"] if r["id"] == test_resource_link.id)
        assert "url" in res and res["url"] is not None

    def test_pdf_resource_has_filename(self, logged_in_client, test_resource_pdf):
        response = logged_in_client.get("/api/resources")
        data = json.loads(response.data)
        res = next(r for r in data["resources"] if r["id"] == test_resource_pdf.id)
        assert "original_filename" in res


class TestCombinedDocumentsEndpoint:
    """GET /api/documents – returns notes + resources in a single list."""

    def test_requires_authentication(self, client):
        response = client.get("/api/documents")
        assert response.status_code in (401, 302)

    def test_returns_ok_when_authenticated(self, logged_in_client):
        response = logged_in_client.get("/api/documents")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "documents" in data

    def test_includes_both_notes_and_resources(
        self, logged_in_client, test_note, test_resource_link
    ):
        response = logged_in_client.get("/api/documents")
        data = json.loads(response.data)
        types = {d["type"] for d in data["documents"]}
        assert "note" in types, "Combined endpoint must include notes"
        assert "resource" in types, "Combined endpoint must include resources"

    def test_each_document_has_type_field(self, logged_in_client, test_note, test_resource_link):
        response = logged_in_client.get("/api/documents")
        data = json.loads(response.data)
        for doc in data["documents"]:
            assert "type" in doc, "Every document in /api/documents must have a 'type' field"
            assert doc["type"] in ("note", "resource")

    def test_filter_by_topic_id(self, logged_in_client, test_note, test_resource_link, test_topic):
        response = logged_in_client.get(f"/api/documents?topic_id={test_topic.id}")
        data = json.loads(response.data)
        for doc in data["documents"]:
            assert doc["topic_id"] == test_topic.id

    def test_documents_sorted_by_updated_at_desc(
        self, logged_in_client, test_note, test_resource_link
    ):
        response = logged_in_client.get("/api/documents")
        data = json.loads(response.data)
        docs = data["documents"]
        if len(docs) > 1:
            # updated_at/created_at should be in descending order
            dates = [d.get("updated_at") or d.get("created_at") for d in docs]
            assert dates == sorted(dates, reverse=True), (
                "Documents should be sorted newest-first"
            )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_topic(db, user_id: int):
    """Helper to create a throwaway topic for isolation tests."""
    from app.models import Topic

    topic = Topic(name="Temp Topic", user_id=user_id)
    db.session.add(topic)
    db.session.commit()
    return topic
