"""
AI utilities for OpenAI integration, token counting, and context management
"""
import tiktoken
from flask import current_app

def count_tokens(text: str, model: str = None) -> int:
    """
    Count the number of tokens in a text string for a given model.
    
    Args:
        text: The text to count tokens for
        model: The model name (defaults to app config)
    
    Returns:
        Number of tokens in the text
    """
    if model is None:
        model = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')
    
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base encoding for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
    """
    Estimate the cost of an OpenAI API call.
    
    Pricing (as of 2026):
    - gpt-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens
    - gpt-4o: $2.50/1M input tokens, $10.00/1M output tokens
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name
    
    Returns:
        Estimated cost in USD
    """
    pricing = {
        "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
        "gpt-4": {"input": 30.00 / 1_000_000, "output": 60.00 / 1_000_000},
    }
    
    model_pricing = pricing.get(model, pricing["gpt-4o-mini"])
    cost = (input_tokens * model_pricing["input"]) + (output_tokens * model_pricing["output"])
    return round(cost, 6)


def truncate_context(messages: list, max_tokens: int, model: str = None) -> list:
    """
    Truncate conversation history to fit within token limit while preserving recent context.
    Always keeps the system message (first message) and recent messages.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        max_tokens: Maximum token budget
        model: Model name
    
    Returns:
        Truncated list of messages
    """
    if not messages:
        return messages
    
    if model is None:
        model = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')
    
    # Always keep system message
    system_message = messages[0] if messages[0].get('role') == 'system' else None
    conversation_messages = messages[1:] if system_message else messages
    
    # Count tokens for system message
    token_count = count_tokens(system_message['content'], model) if system_message else 0
    
    # Add messages from most recent backwards until we hit the limit
    truncated_messages = []
    for message in reversed(conversation_messages):
        message_tokens = count_tokens(message['content'], model) + 4  # +4 for message formatting
        
        if token_count + message_tokens > max_tokens:
            break
        
        token_count += message_tokens
        truncated_messages.insert(0, message)
    
    # Prepend system message if it exists
    if system_message:
        truncated_messages.insert(0, system_message)
    
    return truncated_messages


def build_context_from_notes(notes: list) -> str:
    """
    Build a context string from a list of Note objects.
    
    Args:
        notes: List of Note model instances
    
    Returns:
        Formatted context string
    """
    if not notes:
        return ""
    
    context_parts = ["# User's Notes\n"]
    for note in notes:
        context_parts.append(f"## {note.title}\n")
        context_parts.append(f"{note.content}\n\n")
    
    return "\n".join(context_parts)


def build_context_from_resources(resources: list) -> str:
    """
    Build a context string from a list of Resource objects.
    
    Args:
        resources: List of Resource model instances
    
    Returns:
        Formatted context string
    """
    if not resources:
        return ""
    
    context_parts = ["# User's Resources\n"]
    for resource in resources:
        context_parts.append(f"## {resource.title}\n")
        if resource.is_link():
            context_parts.append(f"Type: Link\nURL: {resource.url}\n\n")
        elif resource.is_pdf():
            context_parts.append(f"Type: PDF Document\nFile: {resource.original_filename}\n")
            # Note: PDF text extraction will be added later
            context_parts.append("(PDF content extraction not yet implemented)\n\n")
    
    return "\n".join(context_parts)
