from .extensions import db
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Topic

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

