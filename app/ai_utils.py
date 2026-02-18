"""
AI utilities for OpenAI integration, token counting, and context management
"""
import tiktoken
from flask import current_app
from typing import List

"""
AI utilities for LLM integration, token counting, and context management.
Supports multiple LLM providers (OpenAI, Ollama) through abstraction layer.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import tiktoken
from flask import current_app


# ============================================================================
# PROVIDER ABSTRACTION LAYER
# ============================================================================

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate chat completion from messages"""
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for this provider's model"""
        pass
    
    @abstractmethod
    def get_context_limit(self) -> int:
        """Get maximum context window size for this provider"""
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference"""
    
    def __init__(self, chat_model: str = "mistral:7b", embedding_model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.chat_model = chat_model
        self.embedding_model = embedding_model
        self.base_url = base_url
        
        try:
            import ollama
            self.client = ollama.Client(host=base_url)
        except ImportError:
            raise ImportError("ollama package not installed. Run: pip install ollama")
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        response = self.client.chat(
            model=self.chat_model,
            messages=messages,
            options={
                'temperature': temperature,
                'num_predict': max_tokens if max_tokens else -1
            }
        )
        return response['message']['content']
    
    def embed(self, text: str) -> List[float]:
        response = self.client.embeddings(
            model=self.embedding_model,
            prompt=text
        )
        return response['embedding']
    
    def count_tokens(self, text: str) -> int:
        return len(text) // 4  # Rough estimation
    
    def get_context_limit(self) -> int:
        context_limits = {
            'mistral': 8192,
            'llama3': 8192,
            'llama2': 4096,
            'phi': 2048,
        }
        base_model = self.chat_model.split(':')[0]
        return context_limits.get(base_model, 8192)


class OpenAIProvider(LLMProvider):
    """OpenAI provider for cloud-based inference"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.model = model
        self.embedding_model = "text-embedding-3-small"
        
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def embed(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        return response.data[0].embedding
    
    def count_tokens(self, text: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    
    def get_context_limit(self) -> int:
        context_limits = {
            'gpt-4o-mini': 128000,
            'gpt-4o': 128000,
            'gpt-4': 8192,
            'gpt-3.5-turbo': 16385,
        }
        return context_limits.get(self.model, 8192)


def get_llm_provider() -> LLMProvider:
    """
    Get the configured LLM provider from Flask app config.
    
    Returns:
        Configured LLMProvider instance
    """
    provider_type = current_app.config.get('LLM_PROVIDER', 'ollama')
    
    if provider_type == 'ollama':
        chat_model = current_app.config.get('OLLAMA_CHAT_MODEL', 'mistral:7b')
        embedding_model = current_app.config.get('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')
        base_url = current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        return OllamaProvider(chat_model, embedding_model, base_url)
    
    elif provider_type == 'openai':
        api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        model = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')
        return OpenAIProvider(api_key, model)
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}")

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


def extract_pdf_text(file_path: str) -> list:
    """Extract text from PDF file with page numbers"""
    import PyPDF2
    
    text_by_page = []
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():  # Only add non-empty pages
                    text_by_page.append({
                        'page': page_num,
                        'text': text.strip()
                    })
        return text_by_page
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return []


def chunk_text(text_by_page: list, chunk_size: int = 500, overlap: int = 100) -> list:
    """
    Chunk text into overlapping segments for RAG processing.
    
    Args:
        text_by_page: List of dicts with 'page' and 'text' keys
        chunk_size: Target size of each chunk in tokens
        overlap: Number of tokens to overlap between chunks
    
    Returns:
        List of chunk dicts with 'chunk_text', 'chunk_index', 'page_number', 'token_count'
    """
    chunks = []
    chunk_index = 0
    
    # Use gpt-3.5-turbo encoding for token counting (compatible with embeddings)
    model = 'gpt-3.5-turbo'
    
    for page_data in text_by_page:
        page_num = page_data['page']
        text = page_data['text']
        
        # Get tokens for this page
        tokens = count_tokens(text, model)
        
        # If page fits in one chunk, add it directly
        if tokens <= chunk_size:
            chunks.append({
                'chunk_text': text,
                'chunk_index': chunk_index,
                'page_number': page_num,
                'token_count': tokens
            })
            chunk_index += 1
            continue
        
        # Split page into overlapping chunks
        words = text.split()
        current_chunk = []
        current_tokens = 0
        
        for word in words:
            # Estimate tokens for word (rough approximation)
            word_tokens = count_tokens(word, model)
            
            if current_tokens + word_tokens > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_text': chunk_text,
                    'chunk_index': chunk_index,
                    'page_number': page_num,
                    'token_count': count_tokens(chunk_text, model)
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_words = []
                overlap_tokens = 0
                for w in reversed(current_chunk):
                    w_tokens = count_tokens(w, model)
                    if overlap_tokens + w_tokens <= overlap:
                        overlap_words.insert(0, w)
                        overlap_tokens += w_tokens
                    else:
                        break
                
                current_chunk = overlap_words
                current_tokens = overlap_tokens
            
            current_chunk.append(word)
            current_tokens += word_tokens
        
        # Add remaining chunk from this page
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_text': chunk_text,
                'chunk_index': chunk_index,
                'page_number': page_num,
                'token_count': count_tokens(chunk_text, model)
            })
            chunk_index += 1
    
    return chunks


def generate_embedding(text: str, max_retries: int = 3) -> list:
    """
    Generate embedding vector for text using configured LLM provider.
    
    Args:
        text: Text to generate embedding for
        max_retries: Maximum number of retry attempts for rate limits
    
    Returns:
        Embedding vector as list (dimension varies by provider)
    
    Raises:
        Exception: If embedding generation fails after retries
    """
    import time
    
    provider = get_llm_provider()
    
    for attempt in range(max_retries):
        try:
            return provider.embed(text)
        except Exception as e:
            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                print(f"Embedding generation failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to generate embedding after {max_retries} attempts: {str(e)}")


# ============================================================================
# RAG (RETRIEVAL AUGMENTED GENERATION) UTILITIES
# ============================================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1, higher is more similar)
    """
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
    
    vec1_arr = np.array(vec1).reshape(1, -1)
    vec2_arr = np.array(vec2).reshape(1, -1)
    
    return float(sklearn_cosine(vec1_arr, vec2_arr)[0][0])


def retrieve_relevant_chunks(query_text: str, resource_ids: List[int], top_k: int = 5, min_similarity: float = 0.3):
    """
    Retrieve most relevant document chunks for a query using RAG.
    
    Args:
        query_text: User's query text
        resource_ids: List of resource IDs to search within
        top_k: Number of top chunks to return
        min_similarity: Minimum similarity threshold (0-1)
        
    Returns:
        List of dicts with chunk info and similarity scores, sorted by relevance
    """
    import json
    from .models import ResourceChunk, Resource
    
    if not resource_ids:
        return []
    
    # Generate embedding for query
    try:
        query_embedding = generate_embedding(query_text)
    except Exception as e:
        print(f"Failed to generate query embedding: {e}")
        return []
    
    # Get all chunks for these resources
    chunks = ResourceChunk.query.filter(
        ResourceChunk.resource_id.in_(resource_ids),
        ResourceChunk.embedding.isnot(None)
    ).all()
    
    if not chunks:
        return []
    
    # Calculate similarity scores
    chunk_scores = []
    for chunk in chunks:
        try:
            # Parse embedding from JSON
            chunk_embedding = json.loads(chunk.embedding)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, chunk_embedding)
            
            if similarity >= min_similarity:
                chunk_scores.append({
                    'chunk': chunk,
                    'similarity': similarity,
                    'text': chunk.chunk_text,
                    'page': chunk.page_number,
                    'resource_id': chunk.resource_id
                })
        except Exception as e:
            print(f"Error processing chunk {chunk.id}: {e}")
            continue
    
    # Sort by similarity (highest first) and take top_k
    chunk_scores.sort(key=lambda x: x['similarity'], reverse=True)
    top_chunks = chunk_scores[:top_k]
    
    # Enrich with resource information
    for item in top_chunks:
        resource = Resource.query.get(item['resource_id'])
        if resource:
            item['resource_title'] = resource.title
            item['resource_filename'] = resource.original_filename
    
    return top_chunks


def build_rag_context(query_text: str, resource_ids: List[int], top_k: int = 5) -> str:
    """
    Build RAG context string from retrieved document chunks.
    
    Args:
        query_text: User's query
        resource_ids: Resources to search in
        top_k: Number of chunks to include
        
    Returns:
        Formatted context string for LLM
    """
    if not resource_ids:
        return ""
    
    retrieved_chunks = retrieve_relevant_chunks(query_text, resource_ids, top_k)
    
    if not retrieved_chunks:
        return ""
    
    context_parts = ["# Retrieved Document Excerpts\n"]
    context_parts.append("The following excerpts from the user's uploaded documents may be relevant:\n")
    
    for i, chunk_data in enumerate(retrieved_chunks, 1):
        resource_name = chunk_data.get('resource_title', 'Unknown')
        page = chunk_data.get('page', '?')
        similarity = chunk_data['similarity']
        text = chunk_data['text']
        
        context_parts.append(f"\n## Excerpt {i} (from '{resource_name}', page {page}, relevance: {similarity:.2f})")
        context_parts.append(f"{text}\n")
    
    context_parts.append("\n---\n")
    context_parts.append("When answering, cite specific excerpts when you reference them (e.g., 'According to Excerpt 1...').\n")
    
    return "\n".join(context_parts)
