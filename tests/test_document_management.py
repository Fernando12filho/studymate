"""
Tests for Note and Resource management.

User story: "A user can attach resources and write notes within a topic."

Routes exercised:

  Notes (app/note.py, prefix /note):
    POST /note/<topic_id>/note             – create note
    POST /note/<note_id>/update            – update title/content
    GET  /note/notes/<note_id>             – view note page
    POST /note/notes/<note_id>/delete      – delete note
    POST /note/preview                     – markdown → HTML preview

  Resources (app/resource.py, prefix /resource):
    POST /resource/<topic_id>/create       – create link / PDF resource
    GET  /resource/<resource_id>/view      – view resource page
    POST /resource/<resource_id>/update    – update title / URL
    POST /resource/<resource_id>/delete    – delete resource (cascades chunks)
    GET  /resource/<resource_id>/download  – download PDF
    GET  /resource/<resource_id>/serve     – serve PDF inline

These tests will FAIL until routes are correctly implemented.
"""

import io
import json
import os
import pytest


# ===========================================================================
# NOTE TESTS
# ===========================================================================

class TestCreateNote:
    """POST /note/<topic_id>/note"""

    def test_requires_authentication(self, client, test_topic):
        r = client.post(
            f"/note/{test_topic.id}/note",
            data=json.dumps({"title": "T", "content": "C"}),
            content_type="application/json",
        )
        assert r.status_code in (401, 302)

    def test_creates_note_and_returns_id(self, logged_in_client, test_topic, db, app, test_user):
        from app.models import Note
        r = logged_in_client.post(
            f"/note/{test_topic.id}/note",
            data=json.dumps({"title": "My Note", "content": "## Hello\n\nContent."}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["success"] is True
        assert "note_id" in data

        with app.app_context():
            note = db.session.get(Note, data["note_id"])
            assert note is not None
            assert note.title == "My Note"
            assert note.user_id == test_user.id
            assert note.topic_id == test_topic.id

    def test_requires_title(self, logged_in_client, test_topic):
        r = logged_in_client.post(
            f"/note/{test_topic.id}/note",
            data=json.dumps({"content": "No title"}),
            content_type="application/json",
        )
        assert r.status_code in (400, 422)

    def test_requires_content(self, logged_in_client, test_topic):
        r = logged_in_client.post(
            f"/note/{test_topic.id}/note",
            data=json.dumps({"title": "No content"}),
            content_type="application/json",
        )
        assert r.status_code in (400, 422)

    def test_rejects_unknown_topic(self, logged_in_client):
        r = logged_in_client.post(
            "/note/999999/note",
            data=json.dumps({"title": "T", "content": "C"}),
            content_type="application/json",
        )
        assert r.status_code in (400, 403, 404)

    def test_rejects_another_users_topic(self, logged_in_client, other_user, db, app):
        from app.models import Topic
        with app.app_context():
            t = Topic(name="Other", user_id=other_user.id)
            db.session.add(t)
            db.session.commit()
            tid = t.id

        r = logged_in_client.post(
            f"/note/{tid}/note",
            data=json.dumps({"title": "Inject", "content": "C"}),
            content_type="application/json",
        )
        assert r.status_code in (400, 403, 404)

    def test_is_ai_generated_defaults_to_false(self, logged_in_client, test_topic, db, app):
        from app.models import Note
        r = logged_in_client.post(
            f"/note/{test_topic.id}/note",
            data=json.dumps({"title": "Human Note", "content": "Written by me"}),
            content_type="application/json",
        )
        data = json.loads(r.data)
        with app.app_context():
            note = db.session.get(Note, data["note_id"])
            assert note.is_ai_generated is False


class TestUpdateNote:
    """POST /note/<note_id>/update"""

    def test_requires_authentication(self, client, test_note):
        r = client.post(
            f"/note/{test_note.id}/update",
            data=json.dumps({"title": "X", "content": "Y"}),
            content_type="application/json",
        )
        assert r.status_code in (401, 302)

    def test_updates_title_and_content(self, logged_in_client, test_note, db, app):
        from app.models import Note
        r = logged_in_client.post(
            f"/note/{test_note.id}/update",
            data=json.dumps({"title": "Updated", "content": "New body"}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["success"] is True

        with app.app_context():
            note = db.session.get(Note, test_note.id)
            assert note.title == "Updated"
            assert note.content == "New body"

    def test_returns_404_for_unknown_note(self, logged_in_client):
        r = logged_in_client.post(
            "/note/999999/update",
            data=json.dumps({"title": "X", "content": "Y"}),
            content_type="application/json",
        )
        assert r.status_code == 404

    def test_cannot_update_another_users_note(self, logged_in_client, other_user, db, app):
        from app.models import Note
        with app.app_context():
            t = _make_topic(db, other_user.id)
            n = Note(title="OK", content="OK", is_ai_generated=False,
                     user_id=other_user.id, topic_id=t.id)
            db.session.add(n)
            db.session.commit()
            nid = n.id

        r = logged_in_client.post(
            f"/note/{nid}/update",
            data=json.dumps({"title": "Hacked", "content": "Hacked"}),
            content_type="application/json",
        )
        assert r.status_code in (403, 404)


class TestViewNote:
    """GET /note/notes/<note_id>"""

    def test_requires_authentication(self, client, test_note):
        r = client.get(f"/note/notes/{test_note.id}", follow_redirects=False)
        assert r.status_code == 302

    def test_renders_note_page(self, logged_in_client, test_note):
        r = logged_in_client.get(f"/note/notes/{test_note.id}")
        assert r.status_code == 200
        html = r.data.decode()
        assert test_note.title in html

    def test_returns_404_for_unknown_note(self, logged_in_client):
        r = logged_in_client.get("/note/notes/999999", follow_redirects=False)
        # Either redirect with flash error or 404
        assert r.status_code in (302, 404)

    def test_cannot_view_another_users_note(self, logged_in_client, other_user, db, app):
        from app.models import Note
        with app.app_context():
            t = _make_topic(db, other_user.id)
            n = Note(title="Secret", content="Secret", is_ai_generated=False,
                     user_id=other_user.id, topic_id=t.id)
            db.session.add(n)
            db.session.commit()
            nid = n.id

        r = logged_in_client.get(f"/note/notes/{nid}", follow_redirects=False)
        assert r.status_code in (302, 403, 404)


class TestDeleteNote:
    """POST /note/notes/<note_id>/delete"""

    def test_requires_authentication(self, client, test_note):
        r = client.post(f"/note/notes/{test_note.id}/delete", follow_redirects=False)
        assert r.status_code == 302

    def test_deletes_note(self, logged_in_client, test_note, db, app):
        from app.models import Note
        r = logged_in_client.post(
            f"/note/notes/{test_note.id}/delete",
            follow_redirects=False,
        )
        assert r.status_code == 302
        with app.app_context():
            assert db.session.get(Note, test_note.id) is None

    def test_returns_404_for_unknown_note(self, logged_in_client):
        r = logged_in_client.post("/note/notes/999999/delete", follow_redirects=False)
        assert r.status_code in (302, 404)

    def test_cannot_delete_another_users_note(self, logged_in_client, other_user, db, app):
        from app.models import Note
        with app.app_context():
            t = _make_topic(db, other_user.id)
            n = Note(title="Keep", content="Keep", is_ai_generated=False,
                     user_id=other_user.id, topic_id=t.id)
            db.session.add(n)
            db.session.commit()
            nid = n.id

        logged_in_client.post(f"/note/notes/{nid}/delete", follow_redirects=False)
        with app.app_context():
            assert db.session.get(Note, nid) is not None


class TestMarkdownPreview:
    """POST /note/preview"""

    def test_requires_authentication(self, client):
        r = client.post(
            "/note/preview",
            data=json.dumps({"content": "# Hello"}),
            content_type="application/json",
        )
        assert r.status_code in (401, 302)

    def test_returns_rendered_html(self, logged_in_client):
        r = logged_in_client.post(
            "/note/preview",
            data=json.dumps({"content": "# Hello\n\nSome **bold** text."}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "html" in data
        assert "<h1>" in data["html"] or "<h" in data["html"]
        assert "bold" in data["html"]

    def test_empty_content_returns_placeholder(self, logged_in_client):
        r = logged_in_client.post(
            "/note/preview",
            data=json.dumps({"content": ""}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "html" in data  # returns a placeholder string, not an error


# ===========================================================================
# RESOURCE TESTS
# ===========================================================================

class TestCreateLinkResource:
    """POST /resource/<topic_id>/create  (resource_type=link)"""

    def test_requires_authentication(self, client, test_topic):
        r = client.post(
            f"/resource/{test_topic.id}/create",
            data={"title": "Article", "resource_type": "link", "url": "https://example.com"},
        )
        assert r.status_code in (401, 302)

    def test_creates_link_resource(self, logged_in_client, test_topic, db, app, test_user):
        from app.models import Resource
        r = logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={
                "title": "My Link",
                "resource_type": "link",
                "url": "https://example.com/article",
            },
            follow_redirects=False,
        )
        assert r.status_code == 302
        with app.app_context():
            res = Resource.query.filter_by(title="My Link", user_id=test_user.id).first()
            assert res is not None
            assert res.resource_type == "link"
            assert res.url == "https://example.com/article"

    def test_requires_title(self, logged_in_client, test_topic):
        r = logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={"resource_type": "link", "url": "https://example.com"},
            follow_redirects=True,
        )
        # Should flash an error and stay on / redirect back to the form
        assert r.status_code in (200, 302)
        html = r.data.decode()
        assert "required" in html.lower() or "error" in html.lower() or "title" in html.lower()

    def test_requires_url_for_link_type(self, logged_in_client, test_topic):
        r = logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={"title": "No URL", "resource_type": "link"},
            follow_redirects=True,
        )
        html = r.data.decode()
        assert "url" in html.lower() or "error" in html.lower()

    def test_rejects_invalid_resource_type(self, logged_in_client, test_topic):
        r = logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={"title": "Bad Type", "resource_type": "docx", "url": "https://x.com"},
            follow_redirects=True,
        )
        html = r.data.decode()
        assert "invalid" in html.lower() or "error" in html.lower()

    def test_rejects_unknown_topic(self, logged_in_client):
        r = logged_in_client.post(
            "/resource/999999/create",
            data={"title": "T", "resource_type": "link", "url": "https://x.com"},
            follow_redirects=True,
        )
        assert r.status_code in (200, 302, 404)

    def test_rejects_another_users_topic(self, logged_in_client, other_user, db, app):
        from app.models import Topic
        with app.app_context():
            t = Topic(name="Other", user_id=other_user.id)
            db.session.add(t)
            db.session.commit()
            tid = t.id

        r = logged_in_client.post(
            f"/resource/{tid}/create",
            data={"title": "Inject", "resource_type": "link", "url": "https://x.com"},
            follow_redirects=True,
        )
        from app.models import Resource
        with app.app_context():
            res = Resource.query.filter_by(title="Inject").first()
            assert res is None


class TestCreatePdfResource:
    """POST /resource/<topic_id>/create  (resource_type=pdf)"""

    def _fake_pdf(self):
        """Return a minimal in-memory file-like object for upload tests."""
        return (io.BytesIO(b"%PDF-1.4 fake pdf content"), "test_upload.pdf")

    def test_creates_pdf_resource(self, logged_in_client, test_topic, db, app, test_user, tmp_path, monkeypatch):
        from app.models import Resource
        import app.resource as resource_module

        # Patch save_uploaded_file so no real disk I/O occurs
        monkeypatch.setattr(
            resource_module,
            "save_uploaded_file",
            lambda file, uid, tid: ("1/1/test.pdf", 1234, "test.pdf"),
        )
        # Also patch ai_utils so the PDF processing pipeline doesn't run
        monkeypatch.setattr("app.resource.ai_utils.extract_pdf_text", lambda p: {1: "Fake text"})
        monkeypatch.setattr("app.resource.ai_utils.chunk_text", lambda pages: [
            {"chunk_text": "Fake text", "chunk_index": 0, "page_number": 1, "token_count": 5}
        ])

        data = {
            "title": "My PDF",
            "resource_type": "pdf",
        }
        r = logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={**data, "file": self._fake_pdf()},
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        assert r.status_code == 302
        with app.app_context():
            res = Resource.query.filter_by(title="My PDF", user_id=test_user.id).first()
            assert res is not None
            assert res.resource_type == "pdf"

    def test_rejects_non_pdf_file(self, logged_in_client, test_topic):
        bad_file = (io.BytesIO(b"not a pdf"), "document.docx")
        r = logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={"title": "Bad File", "resource_type": "pdf", "file": bad_file},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        html = r.data.decode()
        assert "pdf" in html.lower() or "allowed" in html.lower() or "error" in html.lower()

    def test_rejects_missing_file(self, logged_in_client, test_topic):
        r = logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={"title": "No File", "resource_type": "pdf"},
            follow_redirects=True,
        )
        html = r.data.decode()
        assert "error" in html.lower() or "required" in html.lower() or "file" in html.lower()


class TestViewResource:
    """GET /resource/<resource_id>/view"""

    def test_requires_authentication(self, client, test_resource_link):
        r = client.get(f"/resource/{test_resource_link.id}/view", follow_redirects=False)
        assert r.status_code == 302

    def test_renders_resource_page(self, logged_in_client, test_resource_link):
        r = logged_in_client.get(f"/resource/{test_resource_link.id}/view")
        assert r.status_code == 200
        html = r.data.decode()
        assert test_resource_link.title in html

    def test_returns_404_for_unknown_resource(self, logged_in_client):
        r = logged_in_client.get("/resource/999999/view", follow_redirects=False)
        assert r.status_code in (302, 404)

    def test_cannot_view_another_users_resource(self, logged_in_client, other_user, db, app):
        from app.models import Resource
        with app.app_context():
            t = _make_topic(db, other_user.id)
            res = Resource(
                title="Private", resource_type="link",
                url="https://private.example.com",
                user_id=other_user.id, topic_id=t.id,
            )
            db.session.add(res)
            db.session.commit()
            rid = res.id

        r = logged_in_client.get(f"/resource/{rid}/view", follow_redirects=False)
        assert r.status_code in (302, 403, 404)


class TestUpdateResource:
    """POST /resource/<resource_id>/update"""

    def test_requires_authentication(self, client, test_resource_link):
        r = client.post(
            f"/resource/{test_resource_link.id}/update",
            data={"title": "New Title"},
            follow_redirects=False,
        )
        assert r.status_code == 302

    def test_updates_title(self, logged_in_client, test_resource_link, db, app):
        from app.models import Resource
        logged_in_client.post(
            f"/resource/{test_resource_link.id}/update",
            data={"title": "Renamed", "url": test_resource_link.url},
            follow_redirects=False,
        )
        with app.app_context():
            res = db.session.get(Resource, test_resource_link.id)
            assert res.title == "Renamed"

    def test_updates_url_for_link(self, logged_in_client, test_resource_link, db, app):
        from app.models import Resource
        logged_in_client.post(
            f"/resource/{test_resource_link.id}/update",
            data={"title": test_resource_link.title, "url": "https://new-url.example.com"},
            follow_redirects=False,
        )
        with app.app_context():
            res = db.session.get(Resource, test_resource_link.id)
            assert res.url == "https://new-url.example.com"

    def test_cannot_update_another_users_resource(self, logged_in_client, other_user, db, app):
        from app.models import Resource
        with app.app_context():
            t = _make_topic(db, other_user.id)
            res = Resource(
                title="Original", resource_type="link",
                url="https://x.com", user_id=other_user.id, topic_id=t.id,
            )
            db.session.add(res)
            db.session.commit()
            rid = res.id

        logged_in_client.post(
            f"/resource/{rid}/update",
            data={"title": "Hacked"},
            follow_redirects=False,
        )
        with app.app_context():
            res = db.session.get(Resource, rid)
            assert res.title == "Original"


class TestDeleteResource:
    """POST /resource/<resource_id>/delete"""

    def test_requires_authentication(self, client, test_resource_link):
        r = client.post(f"/resource/{test_resource_link.id}/delete", follow_redirects=False)
        assert r.status_code == 302

    def test_deletes_resource(self, logged_in_client, test_resource_link, db, app):
        from app.models import Resource
        r = logged_in_client.post(
            f"/resource/{test_resource_link.id}/delete",
            follow_redirects=False,
        )
        assert r.status_code == 302
        with app.app_context():
            assert db.session.get(Resource, test_resource_link.id) is None

    def test_cascade_deletes_chunks(self, logged_in_client, test_resource_pdf, db, app):
        from app.models import Resource, ResourceChunk
        # Add some chunks for the PDF resource
        with app.app_context():
            for i in range(3):
                chunk = ResourceChunk(
                    resource_id=test_resource_pdf.id,
                    chunk_text=f"Chunk {i}",
                    chunk_index=i,
                )
                db.session.add(chunk)
            db.session.commit()

        logged_in_client.post(
            f"/resource/{test_resource_pdf.id}/delete",
            follow_redirects=False,
        )
        with app.app_context():
            chunks = ResourceChunk.query.filter_by(resource_id=test_resource_pdf.id).all()
            assert len(chunks) == 0, "ResourceChunk rows must be deleted with the resource"

    def test_cannot_delete_another_users_resource(self, logged_in_client, other_user, db, app):
        from app.models import Resource
        with app.app_context():
            t = _make_topic(db, other_user.id)
            res = Resource(
                title="Keep", resource_type="link",
                url="https://x.com", user_id=other_user.id, topic_id=t.id,
            )
            db.session.add(res)
            db.session.commit()
            rid = res.id

        logged_in_client.post(f"/resource/{rid}/delete", follow_redirects=False)
        with app.app_context():
            assert db.session.get(Resource, rid) is not None


class TestServeAndDownloadResource:

    def _write_fake_pdf(self, app, resource):
        """Put a fake PDF file at the path the resource expects."""
        upload_folder = app.config["UPLOAD_FOLDER"]
        full_path = os.path.join(upload_folder, resource.file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(b"%PDF-1.4 fake content")
        return full_path

    def test_serve_requires_authentication(self, client, test_resource_pdf):
        r = client.get(f"/resource/{test_resource_pdf.id}/serve", follow_redirects=False)
        assert r.status_code == 302

    def test_serve_returns_pdf_content_type(self, logged_in_client, test_resource_pdf, app):
        path = self._write_fake_pdf(app, test_resource_pdf)
        try:
            r = logged_in_client.get(f"/resource/{test_resource_pdf.id}/serve")
            assert r.status_code == 200
            assert "pdf" in r.content_type.lower()
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_serve_404_for_missing_file(self, logged_in_client, test_resource_pdf, app):
        upload_folder = app.config["UPLOAD_FOLDER"]
        full_path = os.path.join(upload_folder, test_resource_pdf.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        r = logged_in_client.get(f"/resource/{test_resource_pdf.id}/serve")
        assert r.status_code in (302, 404, 500)  # 500 from send_from_directory on missing file

    def test_serve_rejects_link_resource(self, logged_in_client, test_resource_link):
        r = logged_in_client.get(
            f"/resource/{test_resource_link.id}/serve",
            follow_redirects=True,
        )
        # Should flash an error and redirect, not stream binary data
        assert "pdf" not in r.content_type.lower() or r.status_code in (302, 400)

    def test_download_requires_authentication(self, client, test_resource_pdf):
        r = client.get(f"/resource/{test_resource_pdf.id}/download", follow_redirects=False)
        assert r.status_code == 302

    def test_download_rejects_link_resource(self, logged_in_client, test_resource_link):
        r = logged_in_client.get(
            f"/resource/{test_resource_link.id}/download",
            follow_redirects=True,
        )
        assert "pdf" not in r.content_type.lower() or r.status_code in (302, 400)

    def test_download_sets_attachment_header(self, logged_in_client, test_resource_pdf, app):
        path = self._write_fake_pdf(app, test_resource_pdf)
        try:
            r = logged_in_client.get(f"/resource/{test_resource_pdf.id}/download")
            assert r.status_code == 200
            assert "attachment" in r.headers.get("Content-Disposition", "")
        finally:
            if os.path.exists(path):
                os.remove(path)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_topic(db, user_id: int):
    from app.models import Topic
    t = Topic(name="Temp", user_id=user_id)
    db.session.add(t)
    db.session.commit()
    return t
