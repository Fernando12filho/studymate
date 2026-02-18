# Migration Guide: From Cloud to Local AI

## What Changed?

Studymate has been refactored to support **local-first AI** using Ollama, moving away from mandatory cloud dependencies. This aligns with the project's mission of accessible, privacy-focused learning tools.

## Architecture Changes

### Before (Cloud-Only)
```
User → Flask App → OpenAI API → Response
                 ↓
           (data sent to cloud)
```

### After (Local-First)
```
User → Flask App → Ollama (local) → Response
                 ↓
           (everything stays on device)
```

## Code Changes Summary

### 1. **Abstraction Layer Added** (`app/ai_utils.py`)

**New Classes:**
- `LLMProvider` - Abstract base class
- `OllamaProvider` - Local inference provider
- `OpenAIProvider` - Cloud inference provider (optional)

**Key Function:**
```python
provider = get_llm_provider()  # Returns configured provider
response = provider.chat(messages)  # Works with any provider
embedding = provider.embed(text)   # Works with any provider
```

### 2. **Configuration Updated** (`app/config.py`)

**New Settings:**
```python
LLM_PROVIDER = "ollama"  # or "openai"
OLLAMA_CHAT_MODEL = "mistral:7b"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
OLLAMA_BASE_URL = "http://localhost:11434"
```

### 3. **Chat Refactored** (`app/chat.py`)

**Changes:**
- Removed direct OpenAI imports
- Uses `get_llm_provider()` instead of `get_openai_client()`
- Token counting now provider-agnostic
- Cost = $0 for local inference

### 4. **RAG Fully Implemented** (`app/ai_utils.py`)

**New Functions:**
- `retrieve_relevant_chunks()` - Semantic search through document chunks
- `build_rag_context()` - Build context from top-k relevant chunks
- `cosine_similarity()` - Vector similarity calculation

**Impact:**
- Chat now uses semantic search to find relevant document excerpts
- Citations included in responses
- Much better context relevance than before

### 5. **Embeddings Abstracted** (`app/ai_utils.py`)

**Before:**
```python
client.embeddings.create(input=text, model="text-embedding-3-small")
```

**After:**
```python
provider.embed(text)  # Works with Ollama or OpenAI
```

### 6. **Health Check Added** (`app/routes.py`)

**New Endpoint:**
```
GET /api/health
```

Checks:
- Is Ollama running?
- Are required models available?
- Provider configuration status

### 7. **Dependencies Updated** (`requirements.txt`)

**Added:**
- `ollama==0.4.4` - Local LLM client

**Made Optional:**
- `openai` - Only needed if using cloud provider
- `tiktoken` - Only for OpenAI token counting

## Breaking Changes

### ⚠️ Environment Variables

**Required (if using Ollama):**
```bash
LLM_PROVIDER=ollama
```

**Optional:**
```bash
OLLAMA_CHAT_MODEL=mistral:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### ⚠️ OpenAI Users

If you want to keep using OpenAI:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
```

Everything else stays the same!

### ⚠️ Embeddings Are Not Compatible

**Issue:** OpenAI embeddings (1536 dimensions) ≠ Nomic embeddings (768 dimensions)

**Impact:** If you have existing PDF chunks with OpenAI embeddings, they need to be regenerated.

**Solution:**
```sql
-- Clear old embeddings (run in SQLite)
DELETE FROM resource_chunk;

-- Or regenerate per resource
-- Just re-upload the PDF and it will re-process
```

## Migration Steps

### For Existing Installations

1. **Pull latest code:**
   ```bash
   git pull origin main
   ```

2. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ollama:**
   ```bash
   curl https://ollama.ai/install.sh | sh
   ollama serve
   ```

4. **Pull models:**
   ```bash
   ollama pull mistral:7b
   ollama pull nomic-embed-text
   ```

5. **Update `.env`:**
   ```bash
   echo "LLM_PROVIDER=ollama" >> .env
   ```

6. **Clear old embeddings (optional but recommended):**
   ```bash
   python manage.py shell
   >>> from app.models import ResourceChunk
   >>> from app.extensions import db
   >>> ResourceChunk.query.delete()
   >>> db.session.commit()
   >>> exit()
   ```

7. **Restart app:**
   ```bash
   python manage.py
   ```

8. **Verify health:**
   ```bash
   curl http://localhost:5000/api/health
   ```

### For New Users

Just follow the [Local AI Setup Guide](./local-ai-setup.md) - it's all local by default!

## Data Compatibility

### Database Schema
✅ **No changes** - All existing data (users, topics, notes, resources) is compatible

### Embeddings
⚠️ **Regeneration required** - Existing embeddings need to be regenerated with new model

### Chat History
✅ **Fully compatible** - All chat history displays normally

## Performance Comparison

### OpenAI (gpt-4o-mini)
- Latency: ~500ms-2s
- Cost: $0.15 per 1M input tokens
- Quality: Excellent
- Privacy: Data sent to cloud

### Ollama (mistral:7b)
- Latency: 2-5s (CPU), <1s (GPU)
- Cost: $0 (free)
- Quality: Very good
- Privacy: 100% local

## Testing the Migration

### 1. Test Chat Without Resources
```bash
# Create a topic, start a chat, ask a question
# Should get responses from local model
```

### 2. Test PDF Upload + RAG
```bash
# Upload a PDF (it will chunk and embed locally)
# Start chat, attach the resource
# Ask questions about the document
# Verify it retrieves relevant chunks
```

### 3. Test Health Check
```bash
curl http://localhost:5000/api/health | python -m json.tool
```

Expected output:
```json
{
  "status": "healthy",
  "provider": "ollama",
  "details": {
    "ollama_running": true,
    "chat_model_available": true,
    "embedding_model_available": true
  }
}
```

## Rollback Plan

If you need to rollback to OpenAI:

```bash
# Set environment variable
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-key

# Restart app (no code changes needed)
python manage.py
```

The abstraction layer makes switching seamless!

## Future Compatibility

The provider abstraction layer makes it easy to add more providers:
- Local options: LM Studio, llama.cpp, GPT4All
- Cloud options: Anthropic Claude, Google Gemini, Cohere
- Specialized: Fine-tuned models for education

All providers implement the same interface, so switching is a config change.

## Getting Help

- **Setup Issues:** See [Local AI Setup Guide](./local-ai-setup.md)
- **Performance Issues:** Check hardware requirements (8GB RAM minimum)
- **Model Issues:** Verify models are pulled with `ollama list`
- **Bugs:** Open a GitHub issue

## Contributing

If you test this migration on different hardware, please share:
- Hardware specs (CPU, RAM, GPU)
- Model used
- Performance (response time)
- Any issues encountered

This helps make Studymate more accessible!

---

**Philosophy:** Local AI isn't about replacing cloud services entirely - it's about giving users choice, privacy, and accessibility. The abstraction layer ensures Studymate works well with both approaches.
