"""
Tests for the Chat Right Panel.

The chat back-end (POST /chat/send, GET /chat/history, etc.) is already
implemented in app/chat.py.  However, the front-end currently wires the
send button only to `console.log`.

This file tests:
  1. The existing back-end chat endpoints (correctness / auth)
  2. The "Save AI response as note" flow (new feature)
  3. That the dashboard serves the right HTML hooks for the JS layer to connect

Because the real LLM is disabled in testing (LLM_PROVIDER='stub'),
we use unittest.mock to patch the provider so tests run offline.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stub_provider(response_text: str = "AI response"):
    """Build a mock LLM provider that returns a canned response."""
    provider = MagicMock()
    provider.chat.return_value = response_text
    provider.count_tokens.return_value = 10
    provider.get_context_limit.return_value = 4096
    return provider


# ---------------------------------------------------------------------------
# POST /chat/send
# ---------------------------------------------------------------------------

class TestSendMessageEndpoint:
    """POST /chat/send"""

    def test_requires_authentication(self, client):
        response = client.post(
            "/chat/send",
            data=json.dumps({"message": "Hello"}),
            content_type="application/json",
        )
        assert response.status_code in (401, 302)

    def test_returns_400_for_empty_message(self, logged_in_client):
        with patch("app.chat.get_llm_provider", return_value=_stub_provider()):
            response = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": ""}),
                content_type="application/json",
            )
        assert response.status_code == 400

    def test_successful_message_exchange(self, logged_in_client):
        ai_text = "This is my canned AI answer."
        with patch("app.chat.get_llm_provider", return_value=_stub_provider(ai_text)):
            response = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": "Explain photosynthesis"}),
                content_type="application/json",
            )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "conversation_id" in data
        assert data["assistant_message"]["content"] == ai_text

    def test_response_schema(self, logged_in_client):
        with patch("app.chat.get_llm_provider", return_value=_stub_provider()):
            response = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": "Hello!"}),
                content_type="application/json",
            )
        data = json.loads(response.data)
        required = {"success", "conversation_id", "user_message", "assistant_message", "usage"}
        missing = required - set(data.keys())
        assert not missing, f"POST /chat/send response missing fields: {missing}"

    def test_messages_are_saved_to_database(self, logged_in_client, db, app):
        from app.models import ChatMessage

        with patch("app.chat.get_llm_provider", return_value=_stub_provider("Saved!")):
            response = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": "Will you save this?"}),
                content_type="application/json",
            )
        data = json.loads(response.data)
        conv_id = data["conversation_id"]

        with app.app_context():
            messages = ChatMessage.query.filter_by(conversation_id=conv_id).all()
            assert len(messages) == 2, "Expected one user + one assistant message saved"
            roles = {m.role for m in messages}
            assert roles == {"user", "assistant"}

    def test_conversation_id_is_reused_across_messages(self, logged_in_client):
        """Subsequent messages with the same conversation_id stay in the same thread."""
        with patch("app.chat.get_llm_provider", return_value=_stub_provider("Answer 1")):
            r1 = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": "First question"}),
                content_type="application/json",
            )
        conv_id = json.loads(r1.data)["conversation_id"]

        with patch("app.chat.get_llm_provider", return_value=_stub_provider("Answer 2")):
            r2 = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": "Second question", "conversation_id": conv_id}),
                content_type="application/json",
            )
        assert json.loads(r2.data)["conversation_id"] == conv_id

    def test_send_with_attached_note(self, logged_in_client, test_note):
        with patch("app.chat.get_llm_provider", return_value=_stub_provider("Noted!")):
            response = logged_in_client.post(
                "/chat/send",
                data=json.dumps({
                    "message": "Summarise the attached note",
                    "note_ids": [test_note.id],
                }),
                content_type="application/json",
            )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        # The note should appear in attached_notes of the user message
        attached = data["user_message"]["attached_notes"]
        attached_ids = [n["id"] for n in attached]
        assert test_note.id in attached_ids

    def test_send_with_attached_resource(self, logged_in_client, test_resource_link):
        with patch("app.chat.get_llm_provider", return_value=_stub_provider("Got it!")):
            response = logged_in_client.post(
                "/chat/send",
                data=json.dumps({
                    "message": "What is this resource about?",
                    "resource_ids": [test_resource_link.id],
                }),
                content_type="application/json",
            )
        assert response.status_code == 200
        data = json.loads(response.data)
        attached = data["user_message"]["attached_resources"]
        attached_ids = [r["id"] for r in attached]
        assert test_resource_link.id in attached_ids

    def test_ignores_notes_belonging_to_another_user(
        self, logged_in_client, other_user, db, app, test_topic
    ):
        """Attaching another user's note_id must be silently ignored (not an error,
        but the note must not be included in the context)."""
        from app.models import Note

        with app.app_context():
            t = _make_topic(db, other_user.id)
            private = Note(
                title="Private", content="Secret", is_ai_generated=False,
                user_id=other_user.id, topic_id=t.id
            )
            db.session.add(private)
            db.session.commit()
            private_id = private.id

        with patch("app.chat.get_llm_provider", return_value=_stub_provider()):
            response = logged_in_client.post(
                "/chat/send",
                data=json.dumps({
                    "message": "Tell me about this note",
                    "note_ids": [private_id],
                }),
                content_type="application/json",
            )
        assert response.status_code == 200
        data = json.loads(response.data)
        attached_ids = [n["id"] for n in data["user_message"]["attached_notes"]]
        assert private_id not in attached_ids


# ---------------------------------------------------------------------------
# GET /chat/history
# ---------------------------------------------------------------------------

class TestChatHistoryEndpoint:
    """GET /chat/history"""

    def test_requires_authentication(self, client):
        response = client.get("/chat/history")
        assert response.status_code in (401, 302)

    def test_returns_conversation_list(self, logged_in_client):
        response = logged_in_client.get("/chat/history")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "conversations" in data
        assert isinstance(data["conversations"], list)

    def test_returns_messages_for_conversation(self, logged_in_client, db, app):
        # Create a conversation with a message first
        with patch("app.chat.get_llm_provider", return_value=_stub_provider("Hi!")):
            r = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": "Recall this"}),
                content_type="application/json",
            )
        conv_id = json.loads(r.data)["conversation_id"]

        response = logged_in_client.get(f"/chat/history?conversation_id={conv_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "messages" in data
        assert len(data["messages"]) == 2  # user + assistant

    def test_history_only_returns_own_conversations(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Conversation

        with app.app_context():
            other_conv = Conversation(user_id=other_user.id)
            db.session.add(other_conv)
            db.session.commit()
            other_conv_id = other_conv.id

        response = logged_in_client.get("/chat/history")
        data = json.loads(response.data)
        conv_ids = [c["id"] for c in data["conversations"]]
        assert other_conv_id not in conv_ids


# ---------------------------------------------------------------------------
# POST /chat/clear
# ---------------------------------------------------------------------------

class TestClearConversationEndpoint:

    def test_requires_authentication(self, client):
        response = client.post(
            "/chat/clear",
            data=json.dumps({"conversation_id": 1}),
            content_type="application/json",
        )
        assert response.status_code in (401, 302)

    def test_clears_messages(self, logged_in_client, db, app):
        from app.models import ChatMessage

        # Create a conversation
        with patch("app.chat.get_llm_provider", return_value=_stub_provider("Hey")):
            r = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": "Hello"}),
                content_type="application/json",
            )
        conv_id = json.loads(r.data)["conversation_id"]

        # Clear it
        clear_resp = logged_in_client.post(
            "/chat/clear",
            data=json.dumps({"conversation_id": conv_id}),
            content_type="application/json",
        )
        assert clear_resp.status_code == 200

        with app.app_context():
            count = ChatMessage.query.filter_by(conversation_id=conv_id).count()
            assert count == 0

    def test_cannot_clear_another_users_conversation(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Conversation

        with app.app_context():
            other_conv = Conversation(user_id=other_user.id)
            db.session.add(other_conv)
            db.session.commit()
            other_id = other_conv.id

        response = logged_in_client.post(
            "/chat/clear",
            data=json.dumps({"conversation_id": other_id}),
            content_type="application/json",
        )
        assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# GET /chat/attachments
# ---------------------------------------------------------------------------

class TestGetAttachmentsEndpoint:

    def test_requires_authentication(self, client):
        response = client.get("/chat/attachments")
        assert response.status_code in (401, 302)

    def test_returns_notes_and_resources(self, logged_in_client, test_note, test_resource_link):
        response = logged_in_client.get("/chat/attachments")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "notes" in data
        assert "resources" in data
        note_ids = [n["id"] for n in data["notes"]]
        res_ids = [r["id"] for r in data["resources"]]
        assert test_note.id in note_ids
        assert test_resource_link.id in res_ids


# ---------------------------------------------------------------------------
# Save AI response as note  (new Feature – POST /chat/save-as-note)
# ---------------------------------------------------------------------------

class TestSaveAiResponseAsNote:
    """
    POST /chat/save-as-note
    Body: { "conversation_id": int, "message_id": int, "topic_id": int,
            "title"?: str }
    Creates a Note with is_ai_generated=True from the assistant message content.
    """

    def test_requires_authentication(self, client):
        response = client.post(
            "/chat/save-as-note",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code in (401, 302)

    def test_saves_assistant_message_as_note(self, logged_in_client, test_topic, db, app):
        ai_content = "## Key Concepts\n\nPoint A and Point B are important."

        with patch("app.chat.get_llm_provider", return_value=_stub_provider(ai_content)):
            send_resp = logged_in_client.post(
                "/chat/send",
                data=json.dumps({"message": "Explain key concepts"}),
                content_type="application/json",
            )
        send_data = json.loads(send_resp.data)
        message_id = send_data["assistant_message"]["id"]
        conv_id = send_data["conversation_id"]

        save_resp = logged_in_client.post(
            "/chat/save-as-note",
            data=json.dumps({
                "conversation_id": conv_id,
                "message_id": message_id,
                "topic_id": test_topic.id,
                "title": "Key Concepts Summary",
            }),
            content_type="application/json",
        )
        assert save_resp.status_code in (200, 201)
        note_data = json.loads(save_resp.data)
        assert note_data["is_ai_generated"] is True
        assert note_data["title"] == "Key Concepts Summary"

        from app.models import Note
        with app.app_context():
            note = db.session.get(Note, note_data["id"])
            assert note is not None
            assert note.content == ai_content
            assert note.is_ai_generated is True

    def test_cannot_save_another_users_message(
        self, logged_in_client, other_user, db, app, test_topic
    ):
        from app.models import Conversation, ChatMessage

        with app.app_context():
            conv = Conversation(user_id=other_user.id)
            db.session.add(conv)
            db.session.commit()
            msg = ChatMessage(
                role="assistant", content="Private AI content",
                conversation_id=conv.id, user_id=other_user.id
            )
            db.session.add(msg)
            db.session.commit()
            msg_id = msg.id
            conv_id = conv.id

        response = logged_in_client.post(
            "/chat/save-as-note",
            data=json.dumps({
                "conversation_id": conv_id,
                "message_id": msg_id,
                "topic_id": test_topic.id,
            }),
            content_type="application/json",
        )
        assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Dashboard HTML — chat panel wiring check
# ---------------------------------------------------------------------------

class TestChatPanelHtml:

    def test_right_panel_is_in_dashboard_html(self, logged_in_client):
        """The dashboard must include the chat panel markup."""
        response = logged_in_client.get("/dashboard")
        assert response.status_code == 200
        html = response.data.decode()
        assert 'id="chatPanel"' in html or 'class="chat-panel"' in html

    def test_chat_input_has_id(self, logged_in_client):
        response = logged_in_client.get("/dashboard")
        html = response.data.decode()
        assert 'id="chatInput"' in html

    def test_send_button_has_id(self, logged_in_client):
        response = logged_in_client.get("/dashboard")
        html = response.data.decode()
        assert 'id="sendBtn"' in html

    def test_chat_messages_container_exists(self, logged_in_client):
        response = logged_in_client.get("/dashboard")
        html = response.data.decode()
        assert 'id="chatMessages"' in html


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_topic(db, user_id: int):
    from app.models import Topic
    t = Topic(name="Temp", user_id=user_id)
    db.session.add(t)
    db.session.commit()
    return t
