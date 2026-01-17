import os
from datetime import datetime
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for, current_app, send_from_directory
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from .models import Topic, Resource
from .extensions import db

bp = Blueprint('resource', __name__, url_prefix='/resource')


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file, user_id, topic_id):
    """Save uploaded file and return file path, size, and original filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Create user-specific directory structure
        user_upload_dir = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            str(user_id),
            str(topic_id)
        )
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Add timestamp to avoid filename conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base, ext = os.path.splitext(filename)
        unique_filename = f"{base}_{timestamp}{ext}"
        
        file_path = os.path.join(user_upload_dir, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Return relative path for database storage
        relative_path = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
        return relative_path, file_size, filename
    
    return None, None, None


@bp.route('/<int:topic_id>/create', methods=['GET', 'POST'])
@login_required
def create_resource(topic_id):
    """Create a new resource (PDF or URL)"""
    topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first()
    
    if not topic:
        flash('Topic not found', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'GET':
        return render_template('resource_form.html', topic=topic)
    
    # Handle POST request
    title = request.form.get('title')
    resource_type = request.form.get('resource_type')  # 'link' or 'pdf'
    url = request.form.get('url')
    file = request.files.get('file')
    
    # Validation
    if not title:
        flash('Resource title is required', 'error')
        return redirect(url_for('resource.create_resource', topic_id=topic_id))
    
    if not resource_type or resource_type not in ['link', 'pdf']:
        flash('Invalid resource type', 'error')
        return redirect(url_for('resource.create_resource', topic_id=topic_id))
    
    new_resource = Resource(
        title=title,
        resource_type=resource_type,
        user_id=current_user.id,
        topic_id=topic.id
    )
    
    # Handle URL resource
    if resource_type == 'link':
        if not url:
            flash('URL is required for link resources', 'error')
            return redirect(url_for('resource.create_resource', topic_id=topic_id))
        new_resource.url = url
    
    # Handle PDF file upload
    elif resource_type == 'pdf':
        if not file or file.filename == '':
            flash('PDF file is required', 'error')
            return redirect(url_for('resource.create_resource', topic_id=topic_id))
        
        if not allowed_file(file.filename):
            flash('Only PDF files are allowed', 'error')
            return redirect(url_for('resource.create_resource', topic_id=topic_id))
        
        file_path, file_size, original_filename = save_uploaded_file(
            file, current_user.id, topic.id
        )
        
        if not file_path:
            flash('Failed to upload file', 'error')
            return redirect(url_for('resource.create_resource', topic_id=topic_id))
        
        new_resource.file_path = file_path
        new_resource.file_size = file_size
        new_resource.original_filename = original_filename
    
    try:
        db.session.add(new_resource)
        db.session.commit()
        flash('Resource created successfully!', 'success')
        return redirect(url_for('topic.view_topic', topic_id=topic_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating resource: {str(e)}', 'error')
        return redirect(url_for('resource.create_resource', topic_id=topic_id))


@bp.route('/<int:resource_id>/view')
@login_required
def view_resource(resource_id):
    """View a specific resource"""
    resource = Resource.query.filter_by(id=resource_id, user_id=current_user.id).first()
    
    if not resource:
        flash('Resource not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('resource_view.html', resource=resource)


@bp.route('/<int:resource_id>/update', methods=['GET', 'POST'])
@login_required
def update_resource(resource_id):
    """Update a resource"""
    resource = Resource.query.filter_by(id=resource_id, user_id=current_user.id).first()
    
    if not resource:
        flash('Resource not found', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'GET':
        return render_template('resource_form.html', resource=resource)
    
    # Handle POST request
    title = request.form.get('title')
    
    if not title:
        flash('Resource title is required', 'error')
        return redirect(url_for('resource.update_resource', resource_id=resource_id))
    
    resource.title = title
    
    # Update URL if it's a link resource
    if resource.is_link():
        url = request.form.get('url')
        if url:
            resource.url = url
    
    # Update file if it's a PDF resource and new file is provided
    elif resource.is_pdf():
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Only PDF files are allowed', 'error')
                return redirect(url_for('resource.update_resource', resource_id=resource_id))
            
            # Delete old file
            if resource.file_path:
                old_file_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    resource.file_path
                )
                if os.path.exists(old_file_path):
                    try:
                        os.remove(old_file_path)
                    except Exception as e:
                        print(f"Error deleting old file: {e}")
            
            # Save new file
            file_path, file_size, original_filename = save_uploaded_file(
                file, current_user.id, resource.topic_id
            )
            
            if file_path:
                resource.file_path = file_path
                resource.file_size = file_size
                resource.original_filename = original_filename
    
    resource.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Resource updated successfully!', 'success')
        return redirect(url_for('topic.view_topic', topic_id=resource.topic_id))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating resource: {str(e)}', 'error')
        return redirect(url_for('resource.update_resource', resource_id=resource_id))


@bp.route('/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete_resource(resource_id):
    """Delete a resource and its file if applicable"""
    resource = Resource.query.filter_by(id=resource_id, user_id=current_user.id).first()
    
    if not resource:
        flash('Resource not found', 'error')
        return redirect(url_for('dashboard'))
    
    topic_id = resource.topic_id
    
    # Delete physical file if exists
    if resource.is_pdf() and resource.file_path:
        file_full_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            resource.file_path
        )
        if os.path.exists(file_full_path):
            try:
                os.remove(file_full_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
    
    try:
        db.session.delete(resource)
        db.session.commit()
        flash('Resource deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting resource: {str(e)}', 'error')
    
    return redirect(url_for('topic.view_topic', topic_id=topic_id))


@bp.route('/<int:resource_id>/download')
@login_required
def download_resource(resource_id):
    """Download a PDF resource"""
    resource = Resource.query.filter_by(id=resource_id, user_id=current_user.id).first()
    
    if not resource:
        flash('Resource not found', 'error')
        return redirect(url_for('dashboard'))
    
    if not resource.is_pdf():
        flash('Only PDF resources can be downloaded', 'error')
        return redirect(url_for('resource.view_resource', resource_id=resource_id))
    
    if not resource.file_path:
        flash('File not found', 'error')
        return redirect(url_for('resource.view_resource', resource_id=resource_id))
    
    # Get the directory and filename
    file_directory = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        os.path.dirname(resource.file_path)
    )
    filename = os.path.basename(resource.file_path)
    
    return send_from_directory(
        file_directory,
        filename,
        as_attachment=True,
        download_name=resource.original_filename or filename
    )



