import datetime
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from .models import Topic, Note
from .extensions import db

bp = Blueprint('note', __name__, url_prefix='/note')

@bp.route("/<int:topic_id>/create_note", methods=['GET', 'POST'])
@login_required
def create_note(topic_id) :
    # """Create a new note for a topic"""
    # topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()

    # if not topic:
    #     flash('Topic not found', 'error')
    #     return redirect(url_for('dashboard'))

    # title = request.form.get('title')
    # content = request.form.get('content')

    # new_note = Note(
    #     title=title,
    #     content=content,
    #     user_id=current_user.id,
    #     topic_id=topic.id
    # )

    # db.session.add(new_note)
    # db.session.commit()

    # flash('Note created successfully!', 'success')
    if request.method == 'GET':
        print("Create note for topic:", topic_id)
    return render_template('notes.html', topic_id=topic_id)

@bp.route("/<int:topic_id>/note", methods=["POST"])
@login_required
def save_note(topic_id):
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')

        note = Note(
            title=title,
            content=content,
            user_id=current_user.id,
            topic_id=topic_id
        )

        db.session.add(note)
        db.session.commit()

        # Return the note_id so JavaScript can redirect
        return jsonify({
            'success': True, 
            'note_id': note.id,
            'redirect_url': url_for('note.view_note', note_id=note.id)
        })

@bp.route("<int:note_id>/update", methods=["POST"])
@login_required
def update_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        return jsonify({'success': False, 'error': 'Note not found'}), 404

    if request.method == 'POST':
        data = request.get_json()
        note.title = data.get('title')
        note.content = data.get('content')
        note.updated_at = datetime.datetime.utcnow()  # Update timestamp if you have this field
        db.session.commit()
        return jsonify({'success': True})

# Route to view a specific note
@bp.route("/notes/<int:note_id>")
@login_required
def view_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        flash('Note not found', 'error')
        return redirect(url_for('dashboard'))
    return render_template('notes.html', note=note, topic_id=note.topic_id)


# Route to delete note
@bp.route("/notes/<int:note_id>/delete", methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        flash('Note not found', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(note)
    db.session.commit()

    flash('Note deleted successfully!', 'success')
    return redirect(url_for('topic.view_topic', topic_id=note.topic_id))