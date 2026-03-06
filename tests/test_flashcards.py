"""
Tests for the Flashcard feature.

User story: "A user can study with AI-generated flashcards based on their notes."

STATUS: The `Flashcard` model exists in app/models.py but NO routes have been
        built yet.  Every test here is marked @pytest.mark.skip so they are
        tracked in the suite without blocking CI.

        When you start implementing flashcards, remove the skip markers one by
        one as each endpoint is ready.

API shape expected (to be implemented):
  POST /api/flashcards/generate   – generate cards from a topic/notes via LLM
  GET  /api/flashcards            – list flashcards for current user (filter by topic)
  GET  /api/flashcards/<id>       – single flashcard detail
  POST /api/flashcards/<id>/review – record a review attempt (difficulty + schedule next)
  DELETE /api/flashcards/<id>     – delete a single card
  DELETE /api/flashcards          – delete all cards for a topic
"""

import json
import pytest


# ===========================================================================
# POST /api/flashcards/generate
# ===========================================================================

class TestGenerateFlashcards:

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_requires_authentication(self, client, test_topic):
        r = client.post(
            "/api/flashcards/generate",
            data=json.dumps({"topic_id": test_topic.id, "count": 5}),
            content_type="application/json",
        )
        assert r.status_code in (401, 302)

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_creates_flashcard_rows(self, logged_in_client, test_topic, db, app, test_user):
        from app.models import Flashcard
        r = logged_in_client.post(
            "/api/flashcards/generate",
            data=json.dumps({"topic_id": test_topic.id, "count": 3}),
            content_type="application/json",
        )
        assert r.status_code in (200, 201)
        data = json.loads(r.data)
        assert "flashcards" in data
        assert len(data["flashcards"]) == 3

        with app.app_context():
            cards = Flashcard.query.filter_by(
                topic_id=test_topic.id, user_id=test_user.id
            ).all()
            assert len(cards) == 3

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_each_card_has_question_and_answer(self, logged_in_client, test_topic):
        r = logged_in_client.post(
            "/api/flashcards/generate",
            data=json.dumps({"topic_id": test_topic.id, "count": 2}),
            content_type="application/json",
        )
        data = json.loads(r.data)
        for card in data["flashcards"]:
            assert "question" in card and len(card["question"]) > 0
            assert "answer" in card and len(card["answer"]) > 0

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_requires_topic_id(self, logged_in_client):
        r = logged_in_client.post(
            "/api/flashcards/generate",
            data=json.dumps({"count": 5}),
            content_type="application/json",
        )
        assert r.status_code == 400

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_rejects_another_users_topic(self, logged_in_client, other_user, db, app):
        from app.models import Topic
        with app.app_context():
            t = Topic(name="Other", user_id=other_user.id)
            db.session.add(t)
            db.session.commit()
            tid = t.id

        r = logged_in_client.post(
            "/api/flashcards/generate",
            data=json.dumps({"topic_id": tid, "count": 3}),
            content_type="application/json",
        )
        assert r.status_code in (400, 403, 404)

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_generation_uses_note_context(
        self, logged_in_client, test_topic, test_note
    ):
        """Cards generated from topic notes should reference content in those notes."""
        r = logged_in_client.post(
            "/api/flashcards/generate",
            data=json.dumps({
                "topic_id": test_topic.id,
                "count": 3,
                "note_ids": [test_note.id],
            }),
            content_type="application/json",
        )
        assert r.status_code in (200, 201)
        data = json.loads(r.data)
        assert len(data["flashcards"]) > 0

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_count_defaults_when_not_supplied(self, logged_in_client, test_topic):
        r = logged_in_client.post(
            "/api/flashcards/generate",
            data=json.dumps({"topic_id": test_topic.id}),
            content_type="application/json",
        )
        assert r.status_code in (200, 201)
        data = json.loads(r.data)
        # A sensible default (e.g. 5 or 10) should be used
        assert len(data["flashcards"]) > 0


# ===========================================================================
# GET /api/flashcards
# ===========================================================================

class TestListFlashcards:

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_requires_authentication(self, client):
        r = client.get("/api/flashcards")
        assert r.status_code in (401, 302)

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_returns_only_own_flashcards(
        self, logged_in_client, other_user, db, app, test_topic, test_user
    ):
        from app.models import Flashcard
        with app.app_context():
            t = _make_topic(db, other_user.id)
            other_card = Flashcard(
                question="Q other", answer="A other",
                user_id=other_user.id, topic_id=t.id,
            )
            own_card = Flashcard(
                question="Q mine", answer="A mine",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            db.session.add_all([other_card, own_card])
            db.session.commit()
            other_id = other_card.id
            own_id = own_card.id

        r = logged_in_client.get("/api/flashcards")
        data = json.loads(r.data)
        ids = [c["id"] for c in data["flashcards"]]
        assert own_id in ids
        assert other_id not in ids

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_filter_by_topic_id(self, logged_in_client, test_topic, db, app, test_user):
        from app.models import Flashcard, Topic
        with app.app_context():
            t2 = Topic(name="T2", user_id=test_user.id)
            db.session.add(t2)
            db.session.commit()
            card_t1 = Flashcard(
                question="T1 Q", answer="T1 A",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            card_t2 = Flashcard(
                question="T2 Q", answer="T2 A",
                user_id=test_user.id, topic_id=t2.id,
            )
            db.session.add_all([card_t1, card_t2])
            db.session.commit()

        r = logged_in_client.get(f"/api/flashcards?topic_id={test_topic.id}")
        data = json.loads(r.data)
        for card in data["flashcards"]:
            assert card["topic_id"] == test_topic.id

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_card_schema(self, logged_in_client, test_topic, db, app, test_user):
        from app.models import Flashcard
        with app.app_context():
            card = Flashcard(
                question="What is X?", answer="X is Y.",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            db.session.add(card)
            db.session.commit()

        r = logged_in_client.get("/api/flashcards")
        data = json.loads(r.data)
        c = next(x for x in data["flashcards"] if x["question"] == "What is X?")
        required = {"id", "question", "answer", "difficulty", "topic_id", "created_at"}
        missing = required - set(c.keys())
        assert not missing, f"Flashcard missing fields: {missing}"


# ===========================================================================
# GET /api/flashcards/<id>
# ===========================================================================

class TestGetSingleFlashcard:

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_returns_single_card(self, logged_in_client, test_topic, db, app, test_user):
        from app.models import Flashcard
        with app.app_context():
            card = Flashcard(
                question="Solo Q", answer="Solo A",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            db.session.add(card)
            db.session.commit()
            cid = card.id

        r = logged_in_client.get(f"/api/flashcards/{cid}")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["id"] == cid

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_404_for_unknown(self, logged_in_client):
        r = logged_in_client.get("/api/flashcards/999999")
        assert r.status_code == 404

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_cannot_view_another_users_card(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Flashcard
        with app.app_context():
            t = _make_topic(db, other_user.id)
            card = Flashcard(
                question="Private Q", answer="Private A",
                user_id=other_user.id, topic_id=t.id,
            )
            db.session.add(card)
            db.session.commit()
            cid = card.id

        r = logged_in_client.get(f"/api/flashcards/{cid}")
        assert r.status_code in (403, 404)


# ===========================================================================
# POST /api/flashcards/<id>/review
# ===========================================================================

class TestReviewFlashcard:

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_requires_authentication(self, client):
        r = client.post(
            "/api/flashcards/1/review",
            data=json.dumps({"difficulty": 3}),
            content_type="application/json",
        )
        assert r.status_code in (401, 302)

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_records_difficulty_and_schedules_next_review(
        self, logged_in_client, test_topic, db, app, test_user
    ):
        from app.models import Flashcard
        with app.app_context():
            card = Flashcard(
                question="Review Q", answer="Review A",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            db.session.add(card)
            db.session.commit()
            cid = card.id

        r = logged_in_client.post(
            f"/api/flashcards/{cid}/review",
            data=json.dumps({"difficulty": 4}),
            content_type="application/json",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "next_review_at" in data

        with app.app_context():
            card = db.session.get(Flashcard, cid)
            assert card.difficulty == 4
            assert card.last_reviewed_at is not None
            assert card.next_review_at is not None

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_difficulty_must_be_1_to_5(self, logged_in_client, test_topic, db, app, test_user):
        from app.models import Flashcard
        with app.app_context():
            card = Flashcard(
                question="Range Q", answer="Range A",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            db.session.add(card)
            db.session.commit()
            cid = card.id

        for bad_val in (0, 6, -1, 100):
            r = logged_in_client.post(
                f"/api/flashcards/{cid}/review",
                data=json.dumps({"difficulty": bad_val}),
                content_type="application/json",
            )
            assert r.status_code == 400, f"Expected 400 for difficulty={bad_val}"

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_harder_card_scheduled_sooner_than_easy(
        self, logged_in_client, test_topic, db, app, test_user
    ):
        """Spaced-repetition: a hard card (difficulty=5) should be reviewed sooner
        than an easy card (difficulty=1)."""
        from app.models import Flashcard
        with app.app_context():
            easy = Flashcard(
                question="Easy Q", answer="Easy A",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            hard = Flashcard(
                question="Hard Q", answer="Hard A",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            db.session.add_all([easy, hard])
            db.session.commit()
            easy_id, hard_id = easy.id, hard.id

        logged_in_client.post(
            f"/api/flashcards/{easy_id}/review",
            data=json.dumps({"difficulty": 1}),
            content_type="application/json",
        )
        logged_in_client.post(
            f"/api/flashcards/{hard_id}/review",
            data=json.dumps({"difficulty": 5}),
            content_type="application/json",
        )

        with app.app_context():
            easy_card = db.session.get(Flashcard, easy_id)
            hard_card = db.session.get(Flashcard, hard_id)
            assert hard_card.next_review_at <= easy_card.next_review_at, (
                "Hard cards should be reviewed sooner (shorter interval)"
            )

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_cannot_review_another_users_card(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Flashcard
        with app.app_context():
            t = _make_topic(db, other_user.id)
            card = Flashcard(
                question="Private Q", answer="Private A",
                user_id=other_user.id, topic_id=t.id,
            )
            db.session.add(card)
            db.session.commit()
            cid = card.id

        r = logged_in_client.post(
            f"/api/flashcards/{cid}/review",
            data=json.dumps({"difficulty": 3}),
            content_type="application/json",
        )
        assert r.status_code in (403, 404)


# ===========================================================================
# DELETE /api/flashcards/<id>
# ===========================================================================

class TestDeleteFlashcard:

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_deletes_card(self, logged_in_client, test_topic, db, app, test_user):
        from app.models import Flashcard
        with app.app_context():
            card = Flashcard(
                question="Delete me", answer="Gone",
                user_id=test_user.id, topic_id=test_topic.id,
            )
            db.session.add(card)
            db.session.commit()
            cid = card.id

        r = logged_in_client.delete(f"/api/flashcards/{cid}")
        assert r.status_code in (200, 204)
        with app.app_context():
            assert db.session.get(Flashcard, cid) is None

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_cannot_delete_another_users_card(
        self, logged_in_client, other_user, db, app
    ):
        from app.models import Flashcard
        with app.app_context():
            t = _make_topic(db, other_user.id)
            card = Flashcard(
                question="Keep me", answer="Protected",
                user_id=other_user.id, topic_id=t.id,
            )
            db.session.add(card)
            db.session.commit()
            cid = card.id

        logged_in_client.delete(f"/api/flashcards/{cid}")
        with app.app_context():
            assert db.session.get(Flashcard, cid) is not None


# ===========================================================================
# DELETE /api/flashcards  (bulk delete by topic)
# ===========================================================================

class TestBulkDeleteFlashcards:

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_deletes_all_cards_for_topic(
        self, logged_in_client, test_topic, db, app, test_user
    ):
        from app.models import Flashcard
        with app.app_context():
            for i in range(4):
                db.session.add(Flashcard(
                    question=f"Q{i}", answer=f"A{i}",
                    user_id=test_user.id, topic_id=test_topic.id,
                ))
            db.session.commit()

        r = logged_in_client.delete(
            "/api/flashcards",
            data=json.dumps({"topic_id": test_topic.id}),
            content_type="application/json",
        )
        assert r.status_code in (200, 204)
        with app.app_context():
            remaining = Flashcard.query.filter_by(topic_id=test_topic.id).all()
            assert len(remaining) == 0

    @pytest.mark.skip(reason="Flashcard routes not yet implemented")
    def test_requires_topic_id(self, logged_in_client):
        r = logged_in_client.delete(
            "/api/flashcards",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_topic(db, user_id: int):
    from app.models import Topic
    t = Topic(name="Temp", user_id=user_id)
    db.session.add(t)
    db.session.commit()
    return t
