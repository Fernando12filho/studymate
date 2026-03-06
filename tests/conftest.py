"""
Shared test fixtures and configuration for StudyMate test suite.

Features under test:
  1. Left-panel document listing  (notes + resources via JSON API)
  2. VS Code-like tab system       (document content APIs used by tabs)
  3. AI-generated note saving      (POST /api/notes, is_ai_generated flag)
  4. Chat right panel              (POST /chat/send wired to back-end)
  5. Document viewer API           (GET /api/notes/<id>, GET /api/resources/<id>)
  6. Topic CRUD
  7. Document management (notes + resources)
  8. RAG pipeline
  9. Chat back-end depth
 10. Flashcards (stub spec)

Marker conventions
------------------
  @pytest.mark.integration  – requires a running Ollama instance; skipped in CI
  @pytest.mark.slow         – long-running tests
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash

# ---------------------------------------------------------------------------
# Configuration override that uses an in-memory SQLite database for tests
# ---------------------------------------------------------------------------
class TestingConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "/tmp/studymate_test_uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf"}
    # Disable real LLM calls in tests – use a stub provider
    LLM_PROVIDER = "stub"
    OLLAMA_BASE_URL = "http://localhost:99999"   # unreachable – should never be called
    OPENAI_API_KEY = None
    LOGIN_DISABLED = False


# ---------------------------------------------------------------------------
# App + database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create the Flask application configured for testing (session-scoped)."""
    from app import create_app
    application = create_app(TestingConfig)
    os.makedirs(TestingConfig.UPLOAD_FOLDER, exist_ok=True)
    yield application


@pytest.fixture(scope="session")
def _db(app):
    """Create database tables once for the whole test session."""
    from app.extensions import db as _database
    with app.app_context():
        _database.create_all()
        yield _database
        _database.drop_all()


@pytest.fixture(autouse=True)
def db(app, _db):
    """
    Wrap every single test in a transaction that is rolled back afterwards,
    so tests are fully isolated without recreating schema each time.
    """
    from app.extensions import db as _database
    with app.app_context():
        connection = _database.engine.connect()
        transaction = connection.begin()
        _database.session.bind = connection  # type: ignore[assignment]
        yield _database
        _database.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def client(app):
    """A Flask test client (session-scoped)."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Helper: log in a user via the test client
# ---------------------------------------------------------------------------

def login(client, email: str, password: str):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def logout(client):
    return client.get("/auth/logout", follow_redirects=True)


# ---------------------------------------------------------------------------
# Reusable data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_user(db, app):
    """Create and return a confirmed test user."""
    from app.models import User

    with app.app_context():
        user = User(
            username="testuser",
            email="test@studymate.test",
            password=generate_password_hash("password123"),
        )
        db.session.add(user)
        db.session.commit()
        # Re-query inside the same context to avoid DetachedInstanceError
        return db.session.get(User, user.id)


@pytest.fixture()
def other_user(db, app):
    """A second user to verify ownership / authorization checks."""
    from app.models import User

    with app.app_context():
        user = User(
            username="otheruser",
            email="other@studymate.test",
            password=generate_password_hash("password456"),
        )
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)


@pytest.fixture()
def test_topic(db, app, test_user):
    """Create a topic owned by test_user."""
    from app.models import Topic

    with app.app_context():
        topic = Topic(
            name="Test Topic",
            description="A topic for testing",
            user_id=test_user.id,
        )
        db.session.add(topic)
        db.session.commit()
        return db.session.get(Topic, topic.id)


@pytest.fixture()
def test_note(db, app, test_user, test_topic):
    """Create a regular (human-authored) note."""
    from app.models import Note

    with app.app_context():
        note = Note(
            title="Test Note",
            content="# Heading\n\nSome **markdown** content.",
            is_ai_generated=False,
            user_id=test_user.id,
            topic_id=test_topic.id,
        )
        db.session.add(note)
        db.session.commit()
        return db.session.get(Note, note.id)


@pytest.fixture()
def ai_note(db, app, test_user, test_topic):
    """Create a note that was generated by the AI."""
    from app.models import Note

    with app.app_context():
        note = Note(
            title="AI Generated Note",
            content="## Summary\n\nThis note was generated by the AI assistant.",
            is_ai_generated=True,
            user_id=test_user.id,
            topic_id=test_topic.id,
        )
        db.session.add(note)
        db.session.commit()
        return db.session.get(Note, note.id)


@pytest.fixture()
def test_resource_link(db, app, test_user, test_topic):
    """Create a URL-type resource."""
    from app.models import Resource

    with app.app_context():
        resource = Resource(
            title="Test Link Resource",
            resource_type="link",
            url="https://example.com/article",
            user_id=test_user.id,
            topic_id=test_topic.id,
        )
        db.session.add(resource)
        db.session.commit()
        return db.session.get(Resource, resource.id)


@pytest.fixture()
def test_resource_pdf(db, app, test_user, test_topic):
    """Create a PDF-type resource (file not actually on disk for unit tests)."""
    from app.models import Resource

    with app.app_context():
        resource = Resource(
            title="Test PDF Resource",
            resource_type="pdf",
            file_path="1/1/test_20240101_000000.pdf",
            file_size=12345,
            original_filename="test.pdf",
            user_id=test_user.id,
            topic_id=test_topic.id,
        )
        db.session.add(resource)
        db.session.commit()
        return db.session.get(Resource, resource.id)


@pytest.fixture()
def logged_in_client(app, client, test_user):
    """
    A test client with test_user already authenticated.
    Uses Flask-Login's test utilities via the app context.
    """
    with app.app_context():
        with client.session_transaction() as sess:
            sess["_user_id"] = str(test_user.id)
            sess["_fresh"] = True
    return client


# ---------------------------------------------------------------------------
# Global LLM stub — prevents any test from accidentally calling a real model
# ---------------------------------------------------------------------------

def _make_stub_provider(response_text: str = "Stub AI response."):
    """Return a fully stubbed LLMProvider mock."""
    provider = MagicMock()
    provider.chat.return_value = response_text
    provider.embed.return_value = [0.1] * 768          # nomic-embed-text dim
    provider.count_tokens.return_value = 10
    provider.get_context_limit.return_value = 4096
    return provider


@pytest.fixture(autouse=True)
def stub_llm(request):
    """
    Automatically patch get_llm_provider and generate_embedding for every
    test that is NOT marked @pytest.mark.integration.

    Integration tests opt out of the stub and hit the real Ollama instance.
    """
    if "integration" in request.keywords:
        yield  # let integration tests run unpatched
        return

    stub = _make_stub_provider()
    with patch("app.chat.get_llm_provider", return_value=stub), \
         patch("app.ai_utils.generate_embedding", return_value=[0.1] * 768):
        yield stub
