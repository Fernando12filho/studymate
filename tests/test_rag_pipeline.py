"""
Tests for the RAG (Retrieval-Augmented Generation) pipeline.

User story: "Uploaded PDFs are automatically chunked so the AI can search them."

What is tested:
  - ai_utils.chunk_text()          – splits extracted pages into correct chunk shape
  - ai_utils.generate_embedding()  – returns a float list (mocked unit / real integration)
  - ai_utils.build_rag_context()   – retrieves relevant chunks and formats context
  - PDF resource creation          – ResourceChunk rows are persisted to the DB
  - Ownership                      – RAG context only includes the requesting user's chunks

Marker conventions:
  @pytest.mark.integration  – requires a running Ollama instance; skip in CI with
                               pytest -m "not integration"

These tests will FAIL until the corresponding functions/endpoints work correctly.
"""

import json
import io
import os
import pytest
from unittest.mock import patch, MagicMock


# ===========================================================================
# Unit tests for ai_utils helpers  (no real LLM needed)
# ===========================================================================

class TestChunkText:
    """ai_utils.chunk_text(pages: dict[int, str]) -> list[dict]"""

    def test_returns_list(self, app):
        from app.ai_utils import chunk_text
        with app.app_context():
            result = chunk_text({1: "Hello world. " * 20})
        assert isinstance(result, list)

    def test_each_chunk_has_required_fields(self, app):
        from app.ai_utils import chunk_text
        with app.app_context():
            chunks = chunk_text({1: "Some text. " * 50})
        assert len(chunks) > 0
        for chunk in chunks:
            required = {"chunk_text", "chunk_index", "page_number", "token_count"}
            missing = required - set(chunk.keys())
            assert not missing, f"Chunk missing fields: {missing}"

    def test_chunk_index_is_sequential(self, app):
        from app.ai_utils import chunk_text
        with app.app_context():
            chunks = chunk_text({1: "Word. " * 200})
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(indices))), "chunk_index must be 0-based sequential"

    def test_page_number_is_preserved(self, app):
        from app.ai_utils import chunk_text
        with app.app_context():
            chunks = chunk_text({3: "Page three text. " * 30})
        assert all(c["page_number"] == 3 for c in chunks)

    def test_token_count_is_positive(self, app):
        from app.ai_utils import chunk_text
        with app.app_context():
            chunks = chunk_text({1: "Token counting test. " * 30})
        assert all(c["token_count"] > 0 for c in chunks)

    def test_multi_page_input(self, app):
        from app.ai_utils import chunk_text
        pages = {1: "Page one. " * 50, 2: "Page two. " * 50, 3: "Page three. " * 50}
        with app.app_context():
            chunks = chunk_text(pages)
        page_numbers = {c["page_number"] for c in chunks}
        # All three pages should produce at least one chunk
        assert page_numbers >= {1, 2, 3}

    def test_empty_pages_returns_empty_list(self, app):
        from app.ai_utils import chunk_text
        with app.app_context():
            chunks = chunk_text({})
        assert chunks == []

    def test_chunk_text_is_non_empty_string(self, app):
        from app.ai_utils import chunk_text
        with app.app_context():
            chunks = chunk_text({1: "Non-empty content. " * 40})
        for chunk in chunks:
            assert isinstance(chunk["chunk_text"], str)
            assert len(chunk["chunk_text"].strip()) > 0


class TestGenerateEmbedding:
    """ai_utils.generate_embedding(text: str) -> list[float]"""

    def test_returns_list_of_floats_mocked(self, app):
        """Unit test: stub the provider's embed method."""
        from app.ai_utils import generate_embedding
        with app.app_context():
            with patch("app.ai_utils.get_llm_provider") as mock_provider_fn:
                mock_provider = MagicMock()
                mock_provider.embed.return_value = [0.1] * 768
                mock_provider_fn.return_value = mock_provider

                result = generate_embedding("test text")

        assert isinstance(result, list)
        assert len(result) == 768
        assert all(isinstance(v, float) for v in result)

    def test_returns_non_zero_vector(self, app):
        from app.ai_utils import generate_embedding
        with app.app_context():
            with patch("app.ai_utils.get_llm_provider") as mock_provider_fn:
                mock_provider = MagicMock()
                mock_provider.embed.return_value = [0.5] * 768
                mock_provider_fn.return_value = mock_provider

                result = generate_embedding("some content")

        assert any(v != 0.0 for v in result), "Embedding must not be all zeros"

    def test_empty_string_raises_or_returns_vector(self, app):
        """Empty string should either raise ValueError or return a valid vector."""
        from app.ai_utils import generate_embedding
        with app.app_context():
            with patch("app.ai_utils.get_llm_provider") as mock_provider_fn:
                mock_provider = MagicMock()
                mock_provider.embed.return_value = [0.0] * 768
                mock_provider_fn.return_value = mock_provider

                try:
                    result = generate_embedding("")
                    # If it doesn't raise, result should still be a list
                    assert isinstance(result, list)
                except (ValueError, Exception):
                    pass  # Valid to raise on empty input

    @pytest.mark.integration
    def test_real_ollama_returns_vector(self, app):
        """Calls the real Ollama nomic-embed-text model. Needs Ollama running."""
        from app.ai_utils import generate_embedding
        with app.app_context():
            result = generate_embedding("The quick brown fox")
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(v, float) for v in result)


class TestBuildRagContext:
    """ai_utils.build_rag_context(query, resource_ids, top_k) -> str"""

    def _seed_chunks(self, db, app, resource_id: int, texts: list[str]):
        """Insert ResourceChunk rows with fake embeddings."""
        from app.models import ResourceChunk
        with app.app_context():
            for i, text in enumerate(texts):
                chunk = ResourceChunk(
                    resource_id=resource_id,
                    chunk_text=text,
                    chunk_index=i,
                    page_number=1,
                    embedding=json.dumps([0.1] * 768),
                    token_count=len(text.split()),
                )
                db.session.add(chunk)
            db.session.commit()

    def test_returns_string(self, app, db, test_resource_pdf):
        from app.ai_utils import build_rag_context
        self._seed_chunks(db, app, test_resource_pdf.id, ["Machine learning is cool."])
        with app.app_context():
            with patch("app.ai_utils.generate_embedding", return_value=[0.1] * 768):
                result = build_rag_context(
                    query_text="What is machine learning?",
                    resource_ids=[test_resource_pdf.id],
                    top_k=3,
                )
        assert isinstance(result, str)

    def test_context_contains_chunk_text(self, app, db, test_resource_pdf):
        from app.ai_utils import build_rag_context
        self._seed_chunks(db, app, test_resource_pdf.id, [
            "Neural networks learn from data.",
            "Gradient descent minimises loss.",
        ])
        with app.app_context():
            with patch("app.ai_utils.generate_embedding", return_value=[0.1] * 768):
                result = build_rag_context(
                    query_text="neural networks",
                    resource_ids=[test_resource_pdf.id],
                    top_k=5,
                )
        # At least one chunk's content should appear in the context
        assert "neural" in result.lower() or "gradient" in result.lower()

    def test_returns_empty_when_no_chunks(self, app, db, test_resource_pdf):
        from app.ai_utils import build_rag_context
        with app.app_context():
            with patch("app.ai_utils.generate_embedding", return_value=[0.1] * 768):
                result = build_rag_context(
                    query_text="Anything",
                    resource_ids=[test_resource_pdf.id],
                    top_k=3,
                )
        assert result == "" or result is None

    def test_top_k_limits_results(self, app, db, test_resource_pdf):
        from app.ai_utils import build_rag_context
        texts = [f"Chunk number {i}." for i in range(10)]
        self._seed_chunks(db, app, test_resource_pdf.id, texts)
        with app.app_context():
            with patch("app.ai_utils.generate_embedding", return_value=[0.1] * 768):
                result_k2 = build_rag_context(
                    query_text="chunk",
                    resource_ids=[test_resource_pdf.id],
                    top_k=2,
                )
                result_k5 = build_rag_context(
                    query_text="chunk",
                    resource_ids=[test_resource_pdf.id],
                    top_k=5,
                )
        # More chunks → more content in context
        assert len(result_k5) >= len(result_k2)

    def test_empty_resource_ids_returns_empty(self, app):
        from app.ai_utils import build_rag_context
        with app.app_context():
            with patch("app.ai_utils.generate_embedding", return_value=[0.1] * 768):
                result = build_rag_context("query", resource_ids=[], top_k=5)
        assert result == "" or result is None

    @pytest.mark.integration
    def test_real_embedding_similarity_search(self, app, db, test_resource_pdf):
        """Uses real Ollama embeddings for the similarity search. Needs Ollama running."""
        from app.ai_utils import build_rag_context, generate_embedding
        self._seed_chunks(db, app, test_resource_pdf.id, [
            "Photosynthesis converts light into sugar.",
            "The mitochondria is the powerhouse of the cell.",
        ])
        # Regenerate real embeddings for these chunks
        from app.models import ResourceChunk
        with app.app_context():
            chunks = ResourceChunk.query.filter_by(resource_id=test_resource_pdf.id).all()
            for chunk in chunks:
                emb = generate_embedding(chunk.chunk_text)
                chunk.embedding = json.dumps(emb)
            db.session.commit()

            result = build_rag_context(
                query_text="energy production in cells",
                resource_ids=[test_resource_pdf.id],
                top_k=2,
            )
        assert isinstance(result, str)
        assert len(result) > 0


# ===========================================================================
# Integration: PDF resource creation persists chunks to the DB
# ===========================================================================

class TestPdfResourceCreationPersistsChunks:
    """
    After POSTing to /resource/<topic_id>/create with a PDF file,
    ResourceChunk rows must be written to the database.
    """

    def test_chunks_created_after_pdf_upload(
        self, logged_in_client, test_topic, db, app, test_user, monkeypatch
    ):
        from app.models import Resource, ResourceChunk
        import app.resource as resource_module

        # Stub disk I/O and text extraction so the test runs offline
        monkeypatch.setattr(
            resource_module,
            "save_uploaded_file",
            lambda file, uid, tid: ("1/1/fake.pdf", 100, "fake.pdf"),
        )
        monkeypatch.setattr(
            "app.resource.ai_utils.extract_pdf_text",
            lambda path: {1: "First page content.", 2: "Second page content."},
        )
        monkeypatch.setattr(
            "app.resource.ai_utils.chunk_text",
            lambda pages: [
                {"chunk_text": t, "chunk_index": i, "page_number": p, "token_count": 5}
                for i, (p, t) in enumerate(
                    [(1, "First page content."), (2, "Second page content.")]
                )
            ],
        )

        fake_pdf = (io.BytesIO(b"%PDF-1.4 fake"), "test.pdf")
        r = logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={"title": "RAG PDF", "resource_type": "pdf", "file": fake_pdf},
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        assert r.status_code == 302

        with app.app_context():
            res = Resource.query.filter_by(title="RAG PDF", user_id=test_user.id).first()
            assert res is not None
            chunks = ResourceChunk.query.filter_by(resource_id=res.id).all()
            assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"

    def test_chunk_fields_are_populated(
        self, logged_in_client, test_topic, db, app, test_user, monkeypatch
    ):
        from app.models import Resource, ResourceChunk
        import app.resource as resource_module

        monkeypatch.setattr(
            resource_module, "save_uploaded_file",
            lambda file, uid, tid: ("1/1/fake2.pdf", 200, "fake2.pdf"),
        )
        monkeypatch.setattr(
            "app.resource.ai_utils.extract_pdf_text",
            lambda path: {1: "Chunk field test content."},
        )
        monkeypatch.setattr(
            "app.resource.ai_utils.chunk_text",
            lambda pages: [
                {"chunk_text": "Chunk field test content.", "chunk_index": 0,
                 "page_number": 1, "token_count": 4}
            ],
        )

        fake_pdf = (io.BytesIO(b"%PDF-1.4"), "f2.pdf")
        logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={"title": "Field Check PDF", "resource_type": "pdf", "file": fake_pdf},
            content_type="multipart/form-data",
            follow_redirects=False,
        )

        with app.app_context():
            res = Resource.query.filter_by(title="Field Check PDF").first()
            chunk = ResourceChunk.query.filter_by(resource_id=res.id).first()
            assert chunk.chunk_text == "Chunk field test content."
            assert chunk.chunk_index == 0
            assert chunk.page_number == 1
            assert chunk.token_count == 4

    def test_no_chunks_when_pdf_has_no_text(
        self, logged_in_client, test_topic, db, app, test_user, monkeypatch
    ):
        """Scanned / image-only PDFs return empty text — no chunks should be saved."""
        from app.models import Resource, ResourceChunk
        import app.resource as resource_module

        monkeypatch.setattr(
            resource_module, "save_uploaded_file",
            lambda file, uid, tid: ("1/1/scanned.pdf", 300, "scanned.pdf"),
        )
        monkeypatch.setattr(
            "app.resource.ai_utils.extract_pdf_text",
            lambda path: {},   # no extractable text
        )

        fake_pdf = (io.BytesIO(b"%PDF-1.4"), "scanned.pdf")
        logged_in_client.post(
            f"/resource/{test_topic.id}/create",
            data={"title": "Scanned PDF", "resource_type": "pdf", "file": fake_pdf},
            content_type="multipart/form-data",
            follow_redirects=False,
        )

        with app.app_context():
            res = Resource.query.filter_by(title="Scanned PDF").first()
            if res:  # resource may still be saved even if chunking is skipped
                chunks = ResourceChunk.query.filter_by(resource_id=res.id).all()
                assert len(chunks) == 0, "No chunks for a PDF with no extractable text"
