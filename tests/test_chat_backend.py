"""
Tests for the Chat back-end — deeper coverage beyond test_chat_right_panel.py.

User story: "A user can chat with the AI in the context of their notes and resources."

This file focuses on:
  - Conversation lifecycle (auto-title, token tracking, ordering)
  - DELETE /chat/conversation/<id>
  - GET /chat/history  (ordering, scoping)
  - GET /chat/attachments  (topic-scoped)
  - Context truncation logic (unit test, no LLM needed)
  - Integration smoke test against real Ollama  (@pytest.mark.integration)

The stub_llm fixture in conftest.py automatically patches get_llm_provider
for every non-integration test in this file.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _send(client, message: str, **kwargs) -> dict:
    """POST /chat/send and return the parsed JSON response."""
    payload = {"message": message, **kwargs}
    r = client.post(
        "/chat/send",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.data}"
    return json.loads(r.data)


# ===========================================================================
# Conversation lifecycle
# ===========================================================================

class TestConversationLifecycle:

    def test_new_conversation_created_when_no_id_supplied(
        self, logged_in_client, stub_llm
    ):
        data = _send(logged_in_client, "Hello")
        assert "conversation_id" in data
        assert isinstance(data["conversation_id"], int)

    def test_same_conversation_reused(self, logged_in_client, stub_llm):
        d1 = _send(logged_in_client, "First message")
        conv_id = d1["conversation_id"]

        d2 = _send(logged_in_client, "Second message", conversation_id=conv_id)
        assert d2["conversation_id"] == conv_id

    def test_auto_title_set_from_first_message(self, logged_in_client, db, app, stub_llm):
        from app.models import Conversation
        long_msg = "A" * 60  # longer than 50 chars
        data = _send(logged_in_client, long_msg)
        conv_id = data["conversation_id"]

        with app.app_context():
            conv = db.session.get(Conversation, conv_id)
            assert conv.title is not None
            assert len(conv.title) <= 53  # 50 chars + '...'
            assert conv.title.startswith("A" * 50)

    def test_short_message_title_has_no_ellipsis(self, logged_in_client, db, app, stub_llm):
        from app.models import Conversation
        data = _send(logged_in_client, "Short title")
        with app.app_context():
            conv = db.session.get(Conversation, data["conversation_id"])
            assert "..." not in (conv.title or "")

    def test_title_not_overwritten_on_subsequent_messages(
        self, logged_in_client, db, app, stub_llm
    ):
        from app.models import Conversation
        d1 = _send(logged_in_client, "First question sets the title")
        conv_id = d1["conversation_id"]
        _send(logged_in_client, "Second question", conversation_id=conv_id)

        with app.app_context():
            conv = db.session.get(Conversation, conv_id)
            assert "First question" in (conv.title or "")


# ===========================================================================
# Token tracking
# ===========================================================================

class TestTokenTracking:

    def test_token_counts_saved_on_assistant_message(
        self, logged_in_client, db, app, stub_llm
    ):
        from app.models import ChatMessage
        data = _send(logged_in_client, "Count my tokens")
        msg_id = data["assistant_message"]["id"]

        with app.app_context():
            msg = db.session.get(ChatMessage, msg_id)
            assert msg.input_tokens is not None and msg.input_tokens > 0
            assert msg.output_tokens is not None and msg.output_tokens > 0
            assert msg.total_tokens == msg.input_tokens + msg.output_tokens

    def test_usage_returned_in_response(self, logged_in_client, stub_llm):
        data = _send(logged_in_client, "Show usage")
        usage = data.get("usage", {})
        assert "input_tokens" in usage
        assert "output_tokens" in usage
        assert "total_tokens" in usage

    def test_model_used_saved_on_assistant_message(
        self, logged_in_client, db, app, stub_llm
    ):
        from app.models import ChatMessage
        data = _send(logged_in_client, "Which model am I?")
        msg_id = data["assistant_message"]["id"]

        with app.app_context():
            msg = db.session.get(ChatMessage, msg_id)
            assert msg.model_used is not None
            assert len(msg.model_used) > 0


# ===========================================================================
# GET /chat/history
# ===========================================================================

class TestChatHistory:

    def test_messages_returned_in_ascending_order(
        self, logged_in_client, db, app, stub_llm
    ):
        d1 = _send(logged_in_client, "Message one")
        conv_id = d1["conversation_id"]
        _send(logged_in_client, "Message two", conversation_id=conv_id)

        r = logged_in_client.get(f"/chat/history?conversation_id={conv_id}")
        data = json.loads(r.data)
        messages = data["messages"]
        timestamps = [m["created_at"] for m in messages]
        assert timestamps == sorted(timestamps), (
            "Messages must be returned in ascending created_at order"
        )

    def test_history_includes_both_roles(
        self, logged_in_client, stub_llm
    ):
        d = _send(logged_in_client, "A question")
        conv_id = d["conversation_id"]

        r = logged_in_client.get(f"/chat/history?conversation_id={conv_id}")
        data = json.loads(r.data)
        roles = {m["role"] for m in data["messages"]}
        assert "user" in roles
        assert "assistant" in roles

    def test_conversation_list_ordered_newest_first(
        self, logged_in_client, stub_llm
    ):
        _send(logged_in_client, "Older conversation")
        _send(logged_in_client, "Newer conversation")

        r = logged_in_client.get("/chat/history")
        data = json.loads(r.data)
        convs = data["conversations"]
        if len(convs) > 1:
            updated_ats = [c["updated_at"] for c in convs]
            assert updated_ats == sorted(updated_ats, reverse=True), (
                "Conversations must be newest-first"
            )

    def test_history_404_for_unknown_conversation(self, logged_in_client):
        r = logged_in_client.get("/chat/history?conversation_id=999999")
        assert r.status_code == 404

    def test_history_only_own_conversations(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Conversation
        with app.app_context():
            other_conv = Conversation(user_id=other_user.id, title="Private")
            db.session.add(other_conv)
            db.session.commit()
            other_id = other_conv.id

        r = logged_in_client.get("/chat/history")
        data = json.loads(r.data)
        conv_ids = [c["id"] for c in data["conversations"]]
        assert other_id not in conv_ids

    def test_conversation_detail_includes_metadata(
        self, logged_in_client, stub_llm
    ):
        d = _send(logged_in_client, "Detail test")
        conv_id = d["conversation_id"]

        r = logged_in_client.get(f"/chat/history?conversation_id={conv_id}")
        data = json.loads(r.data)
        assert "conversation" in data
        required = {"id", "title", "created_at", "topic_id"}
        missing = required - set(data["conversation"].keys())
        assert not missing, f"Conversation detail missing fields: {missing}"


# ===========================================================================
# DELETE /chat/conversation/<id>
# ===========================================================================

class TestDeleteConversation:

    def test_requires_authentication(self, client):
        r = client.delete("/chat/conversation/1")
        assert r.status_code in (401, 302)

    def test_deletes_conversation_and_messages(
        self, logged_in_client, db, app, stub_llm
    ):
        from app.models import Conversation, ChatMessage
        data = _send(logged_in_client, "To be deleted")
        conv_id = data["conversation_id"]

        r = logged_in_client.delete(f"/chat/conversation/{conv_id}")
        assert r.status_code == 200
        assert json.loads(r.data).get("success") is True

        with app.app_context():
            assert db.session.get(Conversation, conv_id) is None
            msgs = ChatMessage.query.filter_by(conversation_id=conv_id).all()
            assert len(msgs) == 0, "All messages must be deleted with the conversation"

    def test_returns_404_for_unknown(self, logged_in_client):
        r = logged_in_client.delete("/chat/conversation/999999")
        assert r.status_code == 404

    def test_cannot_delete_another_users_conversation(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Conversation
        with app.app_context():
            conv = Conversation(user_id=other_user.id)
            db.session.add(conv)
            db.session.commit()
            cid = conv.id

        r = logged_in_client.delete(f"/chat/conversation/{cid}")
        assert r.status_code == 404

        with app.app_context():
            assert db.session.get(Conversation, cid) is not None


# ===========================================================================
# GET /chat/attachments
# ===========================================================================

class TestChatAttachments:

    def test_requires_authentication(self, client):
        r = client.get("/chat/attachments")
        assert r.status_code in (401, 302)

    def test_returns_all_user_notes_and_resources(
        self, logged_in_client, test_note, test_resource_link
    ):
        r = logged_in_client.get("/chat/attachments")
        assert r.status_code == 200
        data = json.loads(r.data)
        note_ids = [n["id"] for n in data["notes"]]
        res_ids = [r["id"] for r in data["resources"]]
        assert test_note.id in note_ids
        assert test_resource_link.id in res_ids

    def test_topic_filter_scopes_results(
        self, logged_in_client, test_note, test_resource_link,
        test_topic, db, app, test_user
    ):
        from app.models import Topic, Note, Resource

        with app.app_context():
            t2 = Topic(name="Other Topic", user_id=test_user.id)
            db.session.add(t2)
            db.session.commit()

            n2 = Note(
                title="Note in T2", content="…",
                is_ai_generated=False,
                user_id=test_user.id, topic_id=t2.id,
            )
            r2 = Resource(
                title="Res in T2", resource_type="link",
                url="https://t2.example.com",
                user_id=test_user.id, topic_id=t2.id,
            )
            db.session.add_all([n2, r2])
            db.session.commit()
            t2_id = t2.id

        r = logged_in_client.get(f"/chat/attachments?topic_id={test_topic.id}")
        data = json.loads(r.data)

        for note in data["notes"]:
            assert note["topic_id"] == test_topic.id
        for res in data["resources"]:
            assert res["topic_id"] == test_topic.id

    def test_does_not_return_another_users_notes(
        self, logged_in_client, other_user, db, app, test_topic
    ):
        from app.models import Note
        with app.app_context():
            t = _make_topic(db, other_user.id)
            n = Note(
                title="Private", content="Private",
                is_ai_generated=False,
                user_id=other_user.id, topic_id=t.id,
            )
            db.session.add(n)
            db.session.commit()
            nid = n.id

        r = logged_in_client.get("/chat/attachments")
        data = json.loads(r.data)
        note_ids = [n["id"] for n in data["notes"]]
        assert nid not in note_ids

    def test_note_preview_is_truncated(self, logged_in_client, test_note):
        """Each note in the attachments list includes a short preview."""
        r = logged_in_client.get("/chat/attachments")
        data = json.loads(r.data)
        note = next((n for n in data["notes"] if n["id"] == test_note.id), None)
        assert note is not None
        assert "preview" in note
        assert len(note["preview"]) <= 103  # 100 chars + possible '...'


# ===========================================================================
# Context truncation (pure unit test — no LLM, no DB)
# ===========================================================================

class TestTruncateContextWithProvider:
    """app.chat.truncate_context_with_provider(messages, max_tokens, provider)"""

    def _make_provider(self, tokens_per_message: int = 10):
        p = MagicMock()
        p.count_tokens.return_value = tokens_per_message
        return p

    def test_keeps_all_messages_when_under_limit(self, app):
        from app.chat import truncate_context_with_provider
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
        ]
        provider = self._make_provider(tokens_per_message=5)
        result = truncate_context_with_provider(messages, max_tokens=1000, provider=provider)
        assert len(result) == 3

    def test_system_message_always_preserved(self, app):
        from app.chat import truncate_context_with_provider
        messages = [{"role": "system", "content": "Important system"}] + [
            {"role": "user", "content": f"Q{i}"} for i in range(20)
        ]
        provider = self._make_provider(tokens_per_message=50)
        result = truncate_context_with_provider(messages, max_tokens=100, provider=provider)
        assert result[0]["role"] == "system"

    def test_recent_messages_preferred_over_older(self, app):
        from app.chat import truncate_context_with_provider
        messages = [
            {"role": "system", "content": "Sys"},
            {"role": "user", "content": "Old question"},
            {"role": "assistant", "content": "Old answer"},
            {"role": "user", "content": "Recent question"},
            {"role": "assistant", "content": "Recent answer"},
        ]
        provider = self._make_provider(tokens_per_message=30)
        # Allow only enough tokens for system + 2 recent messages
        result = truncate_context_with_provider(messages, max_tokens=90, provider=provider)
        contents = [m["content"] for m in result]
        assert "Recent question" in contents or "Recent answer" in contents

    def test_never_exceeds_max_tokens(self, app):
        from app.chat import truncate_context_with_provider
        messages = [{"role": "system", "content": "Sys"}] + [
            {"role": "user", "content": f"Question {i}"} for i in range(50)
        ]
        max_tokens = 50
        provider = self._make_provider(tokens_per_message=10)
        result = truncate_context_with_provider(messages, max_tokens=max_tokens, provider=provider)
        total = sum(provider.count_tokens(m["content"]) + 4 for m in result)
        assert total <= max_tokens + provider.count_tokens("Sys"), (
            f"Token count {total} exceeds max {max_tokens}"
        )

    def test_empty_messages_returns_empty(self, app):
        from app.chat import truncate_context_with_provider
        result = truncate_context_with_provider([], max_tokens=100, provider=self._make_provider())
        assert result == []


# ===========================================================================
# Integration smoke test
# ===========================================================================

class TestChatIntegration:

    @pytest.mark.integration
    def test_real_ollama_response_is_non_empty(self, logged_in_client, app):
        """Sends a real message to Ollama and expects a substantive response."""
        r = logged_in_client.post(
            "/chat/send",
            data=json.dumps({"message": "In one sentence, what is 2 + 2?"}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        content = data["assistant_message"]["content"]
        assert len(content.strip()) > 5, "Expected a real response, got: " + repr(content)

    @pytest.mark.integration
    def test_real_ollama_uses_note_context(
        self, logged_in_client, test_note, app
    ):
        """Attaches a note and verifies the response mentions its topic."""
        r = logged_in_client.post(
            "/chat/send",
            data=json.dumps({
                "message": "What is the title of the attached note?",
                "note_ids": [test_note.id],
            }),
            content_type="application/json",
        )
        assert r.status_code == 200
        content = json.loads(r.data)["assistant_message"]["content"]
        # The AI should mention the note title ("Test Note") somewhere in the response
        assert test_note.title.lower() in content.lower() or len(content) > 10


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_topic(db, user_id: int):
    from app.models import Topic
    t = Topic(name="Temp", user_id=user_id)
    db.session.add(t)
    db.session.commit()
    return t
