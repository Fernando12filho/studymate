import datetime
from .extensions import db
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Topic, Note

bp = Blueprint('topics', __name__, url_prefix='/topic')

def get_all_user_topics():
    """Helper function to get all main topics for sidebar"""
    return Topic.query.filter_by(user_id=current_user.id, parent_topic_id=None).order_by(Topic.created_at.desc()).all()

@bp.route("/create", methods=['GET', 'POST'])
@login_required
def create_topic():
    """Create a new topic or subtopic"""
    parent_id = request.args.get('parent_id', type=int)
    parent_topic = None
    
    if parent_id:
        parent_topic = Topic.query.filter_by(id=parent_id, user_id=current_user.id).first()
        if not parent_topic:
            flash('Parent topic not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if parent is already a subtopic (prevent sub-sub-topics)
        if parent_topic.is_subtopic():
            flash('Cannot create a subtopic of a subtopic', 'error')
            return redirect(url_for('topics.view_topic', topic_id=parent_id))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Topic name is required', 'error')
            return render_template('dashboard.html', 
                                   parent_topic=parent_topic,
                                   all_topics=get_all_user_topics(),
                                   current_topic=parent_topic,
                                   active_panel='topics')
        
        new_topic = Topic(
            name=name,
            description=description,
            user_id=current_user.id,
            parent_topic_id=parent_id
        )
        
        db.session.add(new_topic)
        db.session.commit()
        
        flash(f'{"Subtopic" if parent_id else "Topic"} created successfully!', 'success')
        return redirect(url_for('topics.view_topic', topic_id=new_topic.id))
    
    return render_template('dashboard.html', 
                           parent_topic=parent_topic,
                           all_topics=get_all_user_topics(),
                           current_topic=parent_topic,
                           active_panel='topics')

@bp.route("/<int:topic_id>")
@login_required
def view_topic(topic_id):
    print("Viewing topic:", topic_id)
    """View a topic detail page"""
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()
    
    if not topic:
        flash('Topic not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard.html', 
                           topic=topic,
                           all_topics=get_all_user_topics(),
                           current_topic=topic,
                           active_panel='topics', 
                           active_topic=topic)

@bp.route("/<int:topic_id>/update", methods=['GET', 'POST'])
@login_required
def update_topic(topic_id):
    """Update an existing topic"""
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()
    
    if not topic:
        flash('Topic not found', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        topic.name = request.form.get('name', topic.name)
        topic.description = request.form.get('description', topic.description)
        
        db.session.commit()
        flash('Topic updated successfully!', 'success')
        return redirect(url_for('topics.view_topic', topic_id=topic.id))
    
    return render_template('create_topic.html', 
                           topic=topic,
                           all_topics=get_all_user_topics(),
                           current_topic=topic,
                           active_panel='topics')

@bp.route("/<int:topic_id>/delete", methods=['POST'])
@login_required
def delete_topic(topic_id):
    """Delete a topic"""
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()
    
    if not topic:
        flash('Topic not found', 'error')
        return redirect(url_for('dashboard'))
    
    parent_id = topic.parent_topic_id
    db.session.delete(topic)
    db.session.commit()
    
    flash('Topic deleted successfully!', 'success')
    
    # Redirect to parent topic if it was a subtopic, otherwise to dashboard
    if parent_id:
        return redirect(url_for('topics.view_topic', topic_id=parent_id))
    return redirect(url_for('dashboard'))

@bp.route("/<int:topic_id>/subtopics", methods=['GET'])
@login_required
def view_subtopics(topic_id):
    """View all subtopics of a topic"""
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()
    
    if not topic:
        flash('Topic not found', 'error')
        return redirect(url_for('dashboard'))
    
    subtopics = Topic.query.filter_by(parent_topic_id=topic_id).all()
    return render_template('dashboard.html', 
                           topic=topic,
                           subtopics=subtopics,
                           all_topics=get_all_user_topics(),
                           current_topic=topic,
                           active_panel='topics')

@bp.route("/<int:topic_id>/create_subtopic", methods=['POST'])
@login_required
def create_subtopic(topic_id):
    """Add a subtopic to a topic"""
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()
    
    if not topic:
        flash('Topic not found', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        new_subtopic = Topic(
            name=name,
            description=description,
            user_id=current_user.id,
            parent_topic_id=topic.id
        )
        
        db.session.add(new_subtopic)
        db.session.commit()
        
        flash('Subtopic created successfully!', 'success')
        return redirect(url_for('topics.view_topic', topic_id=topic.id))

@bp.route("/<int:topic_id>/delete_subtopic", methods=['POST'])
@login_required
def delete_subtopic(topic_id):
    """Delete a subtopic from a topic"""
    subtopic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()

    if not subtopic:
        flash('Subtopic not found', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(subtopic)
    db.session.commit()

    flash('Subtopic deleted successfully!', 'success')
    return redirect(url_for('topics.view_topic', topic_id=subtopic.parent_topic_id))

@bp.route("/<int:topic_id>/create_note", methods=['GET', 'POST'])
@login_required
def create_note(topic_id):
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

@bp.route("/<int:topic_id>/save_note", methods=['POST'])
@login_required
def save_note(topic_id):
    """Save a note for a topic"""
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()

    if not topic:
        flash('Topic not found', 'error')
        return redirect(url_for('dashboard'))

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    is_ai_generated = data.get('is_ai_generated')

    print("Saving note:", title, content, is_ai_generated)

    new_note = Note(
        title=title,
        content=content,
        is_ai_generated=is_ai_generated,
        user_id=current_user.id,
        topic_id=topic.id
    )

    db.session.add(new_note)
    db.session.commit()

    flash('Note created successfully!', 'success')
    return redirect(url_for('topics.view_topic', topic_id=topic.id))

# Route to view a specific note
@bp.route("/notes/<int:note_id>")
@login_required
def view_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    if not note:
        flash('Note not found', 'error')
        return redirect(url_for('dashboard'))
    return render_template('notes.html', note=note, topic_id=note.topic_id)
