"""
Tests for the Document Viewer API.

Feature: Documents (notes and resources) open inside VS Code-style tabs in the
         main content area.  Each tab fetches its content from a JSON API and
         renders it inline — no full-page navigation.

Endpoints tested here are a superset of those in test_tab_system.py:
  GET /api/notes/<id>
      → Full note payload with rendered HTML, edit metadata, breadcrumb.

  GET /api/resources/<id>
      → Resource metadata + embed/viewer info so the UI can decide HOW to
        render the resource (iframe for PDF, embed for YouTube, link for URL…)

  GET /resource/<id>/serve
      → Serves the raw PDF file (Content-Type: application/pdf).
        Used by the in-tab PDF viewer iframe or download link.

  POST /api/notes/<id>/rename       (optional – inline rename from tab title)
  DELETE /api/notes/<id>            (optional – close & delete from tab context menu)
  DELETE /api/resources/<id>        (optional – same for resources)

These tests will FAIL until the endpoints are implemented.
"""

import json
import io
import pytest


# ---------------------------------------------------------------------------
# Note viewer   GET /api/notes/<id>
# ---------------------------------------------------------------------------

class TestNoteViewerApi:

    def test_requires_auth(self, client, test_note):
        assert client.get(f"/api/notes/{test_note.id}").status_code in (401, 302)

    def test_basic_200(self, logged_in_client, test_note):
        r = logged_in_client.get(f"/api/notes/{test_note.id}")
        assert r.status_code == 200

    def test_returns_json(self, logged_in_client, test_note):
        r = logged_in_client.get(f"/api/notes/{test_note.id}")
        assert r.content_type.startswith("application/json")

    def test_all_viewer_fields_present(self, logged_in_client, test_note):
        data = json.loads(logged_in_client.get(f"/api/notes/{test_note.id}").data)
        required = {
            "id", "title", "content", "content_html",
            "is_ai_generated", "topic_id", "topic_name",
            "created_at", "updated_at",
        }
        missing = required - set(data.keys())
        assert not missing, f"Missing fields in note viewer response: {missing}"

    def test_content_html_is_not_empty(self, logged_in_client, test_note):
        data = json.loads(logged_in_client.get(f"/api/notes/{test_note.id}").data)
        assert data["content_html"].strip() != "", "content_html must not be empty"

    def test_raw_markdown_preserved(self, logged_in_client, test_note):
        """The raw markdown source should also be returned so the editor can load it."""
        data = json.loads(logged_in_client.get(f"/api/notes/{test_note.id}").data)
        # The fixture note has '# Heading' as part of its content
        assert "Heading" in data["content"], "Raw markdown content must be preserved"

    def test_ai_generated_flag_correct_for_human_note(self, logged_in_client, test_note):
        data = json.loads(logged_in_client.get(f"/api/notes/{test_note.id}").data)
        assert data["is_ai_generated"] is False

    def test_ai_generated_flag_correct_for_ai_note(self, logged_in_client, ai_note):
        data = json.loads(logged_in_client.get(f"/api/notes/{ai_note.id}").data)
        assert data["is_ai_generated"] is True

    def test_404_for_unknown_note(self, logged_in_client):
        assert logged_in_client.get("/api/notes/999999").status_code == 404

    def test_cannot_view_other_users_note(self, logged_in_client, other_user, db, app):
        from app.models import Note
        with app.app_context():
            t = _make_topic(db, other_user.id)
            n = Note(title="Private", content="Secret", is_ai_generated=False,
                     user_id=other_user.id, topic_id=t.id)
            db.session.add(n)
            db.session.commit()
            nid = n.id
        assert logged_in_client.get(f"/api/notes/{nid}").status_code in (403, 404)


# ---------------------------------------------------------------------------
# Resource viewer   GET /api/resources/<id>
# ---------------------------------------------------------------------------

class TestResourceViewerApi:

    def test_requires_auth(self, client, test_resource_link):
        assert client.get(f"/api/resources/{test_resource_link.id}").status_code in (401, 302)

    def test_basic_200(self, logged_in_client, test_resource_link):
        assert logged_in_client.get(f"/api/resources/{test_resource_link.id}").status_code == 200

    def test_returns_json(self, logged_in_client, test_resource_link):
        r = logged_in_client.get(f"/api/resources/{test_resource_link.id}")
        assert r.content_type.startswith("application/json")

    def test_link_resource_core_fields(self, logged_in_client, test_resource_link):
        data = json.loads(logged_in_client.get(f"/api/resources/{test_resource_link.id}").data)
        required = {"id", "title", "resource_type", "url", "topic_id", "topic_name", "created_at"}
        missing = required - set(data.keys())
        assert not missing, f"Missing fields in link resource viewer: {missing}"

    def test_link_resource_has_correct_type(self, logged_in_client, test_resource_link):
        data = json.loads(logged_in_client.get(f"/api/resources/{test_resource_link.id}").data)
        assert data["resource_type"] == "link"

    def test_pdf_resource_core_fields(self, logged_in_client, test_resource_pdf):
        data = json.loads(logged_in_client.get(f"/api/resources/{test_resource_pdf.id}").data)
        required = {
            "id", "title", "resource_type",
            "original_filename", "file_size",
            "topic_id", "topic_name",
        }
        missing = required - set(data.keys())
        assert not missing, f"Missing fields in PDF resource viewer: {missing}"

    def test_pdf_resource_has_viewer_url(self, logged_in_client, test_resource_pdf):
        data = json.loads(logged_in_client.get(f"/api/resources/{test_resource_pdf.id}").data)
        has_viewer = "viewer_url" in data or "file_url" in data
        assert has_viewer, "PDF resource must include viewer_url or file_url"

    def test_resource_includes_summary_if_available(self, logged_in_client, db, app, test_resource_pdf):
        """If the resource has an AI-generated summary, it should be included."""
        from app.models import Resource
        with app.app_context():
            res = db.session.get(Resource, test_resource_pdf.id)
            res.summary = "This PDF discusses machine learning fundamentals."
            db.session.commit()

        data = json.loads(logged_in_client.get(f"/api/resources/{test_resource_pdf.id}").data)
        assert "summary" in data
        assert "machine learning" in data["summary"]

    def test_404_for_unknown_resource(self, logged_in_client):
        assert logged_in_client.get("/api/resources/999999").status_code == 404

    def test_cannot_view_other_users_resource(self, logged_in_client, other_user, db, app):
        from app.models import Resource
        with app.app_context():
            t = _make_topic(db, other_user.id)
            r = Resource(
                title="Private Resource", resource_type="link",
                url="https://private.example.com",
                user_id=other_user.id, topic_id=t.id
            )
            db.session.add(r)
            db.session.commit()
            rid = r.id
        assert logged_in_client.get(f"/api/resources/{rid}").status_code in (403, 404)


# ---------------------------------------------------------------------------
# PDF file serving   GET /resource/<id>/serve
# ---------------------------------------------------------------------------

class TestPdfServeEndpoint:
    """This endpoint streams the raw PDF bytes for the in-tab viewer."""

    def test_requires_auth(self, client, test_resource_pdf):
        r = client.get(f"/resource/{test_resource_pdf.id}/serve")
        assert r.status_code in (401, 302)

    def test_returns_404_for_nonpdf_resource(self, logged_in_client, test_resource_link):
        """Link resources have no file to serve."""
        r = logged_in_client.get(f"/resource/{test_resource_link.id}/serve")
        assert r.status_code == 404

    def test_returns_pdf_content_type_when_file_exists(
        self, logged_in_client, test_resource_pdf, tmp_path, app
    ):
        """
        Creates a fake PDF file at the expected path then verifies the endpoint
        returns Content-Type: application/pdf.
        """
        import os
        from app.models import Resource
        from app.config import Config

        upload_folder = app.config["UPLOAD_FOLDER"]
        fake_pdf_path = os.path.join(
            upload_folder, test_resource_pdf.file_path
        )
        os.makedirs(os.path.dirname(fake_pdf_path), exist_ok=True)
        with open(fake_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4 fake content")

        try:
            r = logged_in_client.get(f"/resource/{test_resource_pdf.id}/serve")
            assert r.status_code == 200
            assert "pdf" in r.content_type.lower()
        finally:
            if os.path.exists(fake_pdf_path):
                os.remove(fake_pdf_path)

    def test_returns_404_when_file_missing(self, logged_in_client, test_resource_pdf):
        """If the file is missing on disk, the endpoint must return 404."""
        import os
        from app.config import Config

        upload_folder = logged_in_client.application.config["UPLOAD_FOLDER"]
        fake_path = os.path.join(upload_folder, test_resource_pdf.file_path)
        # Ensure it does NOT exist
        if os.path.exists(fake_path):
            os.remove(fake_path)

        r = logged_in_client.get(f"/resource/{test_resource_pdf.id}/serve")
        assert r.status_code == 404

    def test_cannot_serve_another_users_pdf(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Resource
        with app.app_context():
            t = _make_topic(db, other_user.id)
            private_pdf = Resource(
                title="Private PDF",
                resource_type="pdf",
                file_path="99/99/secret.pdf",
                file_size=1000,
                original_filename="secret.pdf",
                user_id=other_user.id,
                topic_id=t.id,
            )
            db.session.add(private_pdf)
            db.session.commit()
            rid = private_pdf.id

        r = logged_in_client.get(f"/resource/{rid}/serve")
        assert r.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Inline note rename   POST /api/notes/<id>/rename
# ---------------------------------------------------------------------------

class TestNoteRenameEndpoint:
    """PATCH or POST /api/notes/<id>/rename — lets tab title be edited."""

    def test_requires_authentication(self, client, test_note):
        r = client.post(
            f"/api/notes/{test_note.id}/rename",
            data=json.dumps({"title": "New Title"}),
            content_type="application/json",
        )
        assert r.status_code in (401, 302)

    def test_renames_note(self, logged_in_client, test_note, db, app):
        r = logged_in_client.post(
            f"/api/notes/{test_note.id}/rename",
            data=json.dumps({"title": "Renamed Title"}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["title"] == "Renamed Title"

    def test_rejects_empty_title(self, logged_in_client, test_note):
        r = logged_in_client.post(
            f"/api/notes/{test_note.id}/rename",
            data=json.dumps({"title": ""}),
            content_type="application/json",
        )
        assert r.status_code == 400

    def test_cannot_rename_other_users_note(self, logged_in_client, other_user, db, app):
        from app.models import Note
        with app.app_context():
            t = _make_topic(db, other_user.id)
            n = Note(title="X", content="Y", is_ai_generated=False,
                     user_id=other_user.id, topic_id=t.id)
            db.session.add(n)
            db.session.commit()
            nid = n.id
        r = logged_in_client.post(
            f"/api/notes/{nid}/rename",
            data=json.dumps({"title": "Hacked"}),
            content_type="application/json",
        )
        assert r.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Delete document via tab close-menu
# ---------------------------------------------------------------------------

class TestDeleteDocumentEndpoint:

    def test_delete_note_requires_auth(self, client, test_note):
        r = client.delete(f"/api/notes/{test_note.id}")
        assert r.status_code in (401, 302)

    def test_delete_note(self, logged_in_client, test_note, db, app):
        from app.models import Note
        r = logged_in_client.delete(f"/api/notes/{test_note.id}")
        assert r.status_code in (200, 204)
        with app.app_context():
            assert db.session.get(Note, test_note.id) is None

    def test_delete_resource_requires_auth(self, client, test_resource_link):
        r = client.delete(f"/api/resources/{test_resource_link.id}")
        assert r.status_code in (401, 302)

    def test_delete_resource(self, logged_in_client, test_resource_link, db, app):
        from app.models import Resource
        r = logged_in_client.delete(f"/api/resources/{test_resource_link.id}")
        assert r.status_code in (200, 204)
        with app.app_context():
            assert db.session.get(Resource, test_resource_link.id) is None

    def test_cannot_delete_another_users_note(self, logged_in_client, other_user, db, app):
        from app.models import Note
        with app.app_context():
            t = _make_topic(db, other_user.id)
            n = Note(title="X", content="Y", is_ai_generated=False,
                     user_id=other_user.id, topic_id=t.id)
            db.session.add(n)
            db.session.commit()
            nid = n.id
        r = logged_in_client.delete(f"/api/notes/{nid}")
        assert r.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_topic(db, user_id: int):
    from app.models import Topic
    t = Topic(name="Temp", user_id=user_id)
    db.session.add(t)
    db.session.commit()
    return t
