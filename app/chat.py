"""
Chat routes for AI-powered study assistant with flexible LLM provider support
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from .models import Conversation, ChatMessage, Note, Resource
from .extensions import db
from .ai_utils import (
    get_llm_provider,
    build_context_from_notes,
    build_rag_context
)

bp = Blueprint('chat', __name__, url_prefix='/chat')


def get_system_prompt():
    """Get the system prompt for the AI assistant"""
    return """You are an AI study assistant integrated into StudyMate, a learning management application. Your role is to help users with their studies by:

1. Answering questions about their notes and learning materials
2. Explaining concepts in clear, educational ways
3. Generating practice exercises and questions
4. Providing study tips and learning strategies
5. Helping break down complex topics

Guidelines:
- Be encouraging and supportive
- Ask clarifying questions when needed
- Reference the user's attached notes/resources when relevant
- Provide structured, well-formatted responses using markdown
- For math/technical content, use proper notation
- Don't do homework for them - guide them to understand
- If you don't have enough context, ask for more information

The user can attach notes and resources to provide context. Use this context to give personalized, relevant answers."""


def get_or_create_conversation(conversation_id=None, topic_id=None):
    """Get existing conversation or create a new one"""
    if conversation_id:
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        if conversation:
            return conversation
    
    # Create new conversation
    conversation = Conversation(
        user_id=current_user.id,
        topic_id=topic_id
    )
    db.session.add(conversation)
    db.session.commit()
    return conversation


def build_messages_for_llm(conversation, user_message, attached_note_ids, attached_resource_ids, provider):
    """Build the messages array for LLM API including context from attachments"""
    messages = []
    
    # Add system message
    messages.append({
        'role': 'system',
        'content': get_system_prompt()
    })
    
    # Load conversation history (excluding current message)
    history = ChatMessage.query.filter_by(
        conversation_id=conversation.id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    for msg in history:
        messages.append({
            'role': msg.role,
            'content': msg.content
        })
    
    # Build context from attachments
    context_parts = []
    
    if attached_note_ids:
        notes = Note.query.filter(
            Note.id.in_(attached_note_ids),
            Note.user_id == current_user.id
        ).all()
        if notes:
            context_parts.append(build_context_from_notes(notes))
    
    # Use RAG to retrieve relevant chunks from attached resources
    if attached_resource_ids:
        rag_context = build_rag_context(
            query_text=user_message,
            resource_ids=attached_resource_ids,
            top_k=5  # Retrieve top 5 most relevant chunks
        )
        if rag_context:
            context_parts.append(rag_context)
    
    # Combine user message with context
    full_message = user_message
    if context_parts:
        context = "\n\n".join(context_parts)
        full_message = f"{context}\n\n---\n\nUser Question: {user_message}"
    
    messages.append({
        'role': 'user',
        'content': full_message
    })
    
    # Truncate if needed to fit token limits
    max_tokens = int(provider.get_context_limit() * 0.5)  # Use 50% for context, leave room for response
    messages = truncate_context_with_provider(messages, max_tokens, provider)
    
    return messages


def truncate_context_with_provider(messages, max_tokens, provider):
    """Truncate conversation history to fit within token limit while preserving recent context"""
    if not messages:
        return messages
    
    # Always keep system message
    system_message = messages[0] if messages[0].get('role') == 'system' else None
    conversation_messages = messages[1:] if system_message else messages
    
    # Count tokens for system message
    token_count = provider.count_tokens(system_message['content']) if system_message else 0
    
    # Add messages from most recent backwards until we hit the limit
    truncated_messages = []
    for message in reversed(conversation_messages):
        message_tokens = provider.count_tokens(message['content']) + 4  # +4 for message formatting
        
        if token_count + message_tokens > max_tokens:
            break
        
        token_count += message_tokens
        truncated_messages.insert(0, message)
    
    # Prepend system message if it exists
    if system_message:
        truncated_messages.insert(0, system_message)
    
    return truncated_messages


@bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send a message to the AI assistant and get a response"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        topic_id = data.get('topic_id')
        attached_note_ids = data.get('note_ids', [])
        attached_resource_ids = data.get('resource_ids', [])
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get or create conversation
        conversation = get_or_create_conversation(conversation_id, topic_id)
        
        # Save user message to database
        user_msg = ChatMessage(
            role='user',
            content=user_message,
            conversation_id=conversation.id,
            user_id=current_user.id
        )
        
        # Attach notes and resources
        if attached_note_ids:
            notes = Note.query.filter(
                Note.id.in_(attached_note_ids),
                Note.user_id == current_user.id
            ).all()
            user_msg.attached_notes.extend(notes)
        
        if attached_resource_ids:
            resources = Resource.query.filter(
                Resource.id.in_(attached_resource_ids),
                Resource.user_id == current_user.id
            ).all()
            user_msg.attached_resources.extend(resources)
        
        db.session.add(user_msg)
        db.session.commit()
        
        # Get LLM provider
        provider = get_llm_provider()
        
        # Build messages for LLM
        messages = build_messages_for_llm(
            conversation, 
            user_message, 
            attached_note_ids, 
            attached_resource_ids,
            provider
        )
        
        # Call LLM API
        temperature = current_app.config.get('OPENAI_TEMPERATURE', 0.7)
        assistant_message = provider.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        
        # Calculate token usage (approximate for local models)
        input_text = '\n'.join([m['content'] for m in messages])
        input_tokens = provider.count_tokens(input_text)
        output_tokens = provider.count_tokens(assistant_message)
        total_tokens = input_tokens + output_tokens
        
        # Get model identifier
        provider_type = current_app.config.get('LLM_PROVIDER', 'ollama')
        if provider_type == 'ollama':
            model_used = current_app.config.get('OLLAMA_CHAT_MODEL', 'mistral:7b')
            cost = 0.0  # Local inference = free
        else:
            model_used = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')
            # Estimate cost for OpenAI (keeping legacy function for OpenAI)
            from .ai_utils import estimate_cost
            cost = estimate_cost(input_tokens, output_tokens, model_used)
        
        # Save assistant response to database
        assistant_msg = ChatMessage(
            role='assistant',
            content=assistant_message,
            conversation_id=conversation.id,
            user_id=current_user.id,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens
        )
        db.session.add(assistant_msg)
        
        # Update conversation title if it's the first message
        if not conversation.title and len(conversation.messages) <= 2:
            # Use first 50 chars of user message as title
            conversation.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'user_message': user_msg.to_dict(),
            'assistant_message': assistant_msg.to_dict(),
            'usage': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'estimated_cost': cost
            }
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'An error occurred processing your message'}), 500


@bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """Get chat history for the current user"""
    conversation_id = request.args.get('conversation_id', type=int)
    
    if conversation_id:
        # Get specific conversation
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        messages = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return jsonify({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat(),
                'topic_id': conversation.topic_id
            },
            'messages': [msg.to_dict() for msg in messages]
        })
    else:
        # Get all conversations for user
        conversations = Conversation.query.filter_by(
            user_id=current_user.id
        ).order_by(Conversation.updated_at.desc()).limit(20).all()
        
        return jsonify({
            'conversations': [
                {
                    'id': conv.id,
                    'title': conv.title or 'New Conversation',
                    'created_at': conv.created_at.isoformat(),
                    'updated_at': conv.updated_at.isoformat(),
                    'message_count': len(conv.messages),
                    'topic_id': conv.topic_id
                }
                for conv in conversations
            ]
        })


@bp.route('/conversation/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    """Delete a conversation and all its messages"""
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        user_id=current_user.id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/clear', methods=['POST'])
@login_required
def clear_current_conversation():
    """Clear the current conversation (delete all messages but keep conversation)"""
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'error': 'conversation_id is required'}), 400
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        user_id=current_user.id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    # Delete all messages
    ChatMessage.query.filter_by(conversation_id=conversation_id).delete()
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/attachments', methods=['GET'])
@login_required
def get_available_attachments():
    """Get all notes and resources available for attachment"""
    topic_id = request.args.get('topic_id', type=int)
    
    # Build query for notes
    notes_query = Note.query.filter_by(user_id=current_user.id)
    if topic_id:
        notes_query = notes_query.filter_by(topic_id=topic_id)
    notes = notes_query.order_by(Note.updated_at.desc()).all()
    
    # Build query for resources
    resources_query = Resource.query.filter_by(user_id=current_user.id)
    if topic_id:
        resources_query = resources_query.filter_by(topic_id=topic_id)
    resources = resources_query.order_by(Resource.updated_at.desc()).all()
    
    return jsonify({
        'notes': [
            {
                'id': note.id,
                'title': note.title,
                'topic_id': note.topic_id,
                'preview': note.content[:100] + ('...' if len(note.content) > 100 else ''),
                'updated_at': note.updated_at.isoformat()
            }
            for note in notes
        ],
        'resources': [
            {
                'id': res.id,
                'title': res.title,
                'type': res.resource_type,
                'topic_id': res.topic_id,
                'url': res.url if res.is_link() else None,
                'updated_at': res.updated_at.isoformat()
            }
            for res in resources
        ]
    })
