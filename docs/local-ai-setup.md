# Local AI Setup Guide

## Overview

Studymate now supports **local, privacy-first AI** using Ollama. This means:
- ✅ No cloud API costs
- ✅ Complete data privacy - everything runs on your machine
- ✅ Works offline once models are downloaded
- ✅ Accessible to anyone with a decent laptop (8-16GB RAM)

## Prerequisites

**Hardware Requirements:**
- **Minimum:** 8GB RAM, 10GB free disk space
- **Recommended:** 16GB RAM, 20GB free disk space
- GPU is optional but improves performance significantly

**Supported Operating Systems:**
- macOS (Apple Silicon or Intel)
- Linux
- Windows (WSL2 or native)

## Step 1: Install Ollama

Ollama is a local LLM runner that manages models and provides an API.

### macOS
```bash
# Download and install from ollama.ai
curl https://ollama.ai/install.sh | sh

# Or use Homebrew
brew install ollama
```

### Linux
```bash
curl https://ollama.ai/install.sh | sh
```

### Windows
Download the installer from [ollama.ai](https://ollama.ai) or use WSL2 with the Linux instructions.

## Step 2: Start Ollama Service

```bash
ollama serve
```

This starts the Ollama API server on `http://localhost:11434`. Keep this terminal running.

## Step 3: Download Required Models

Open a new terminal and pull the required models:

### Chat Model (choose one)

**Mistral 7B** (Recommended - best balance of quality and speed):
```bash
ollama pull mistral:7b
```

**Alternative Options:**
```bash
# Smaller, faster, lower quality
ollama pull phi:3b

# Larger, better quality, slower
ollama pull llama3:8b
```

### Embedding Model

**Nomic Embed Text** (Recommended for document embeddings):
```bash
ollama pull nomic-embed-text
```

**Verify Installation:**
```bash
ollama list
```

You should see both models listed.

## Step 4: Install Python Dependencies

```bash
cd /path/to/studymate
pip install -r requirements.txt
```

This installs the `ollama` Python client and other dependencies.

## Step 5: Configure Studymate

Create or edit `.env` file in the project root:

```bash
# LLM Provider Configuration
LLM_PROVIDER=ollama

# Ollama Settings (use defaults or customize)
OLLAMA_CHAT_MODEL=mistral:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434

# Optional: OpenAI fallback (if you still want cloud option)
# OPENAI_API_KEY=your-api-key-here
```

## Step 6: Verify Setup

Start the Flask application:
```bash
python manage.py
```

Check the health endpoint:
```bash
curl http://localhost:5000/api/health | python -m json.tool
```

**Healthy Response:**
```json
{
  "status": "healthy",
  "provider": "ollama",
  "details": {
    "ollama_running": true,
    "chat_model": "mistral:7b",
    "chat_model_available": true,
    "embedding_model": "nomic-embed-text",
    "embedding_model_available": true,
    "available_models": ["mistral:7b", "nomic-embed-text"]
  }
}
```

**Common Issues:**

❌ `"ollama_running": false`
- **Fix:** Make sure `ollama serve` is running in another terminal

❌ `"chat_model_available": false`
- **Fix:** Run `ollama pull mistral:7b`

❌ `"embedding_model_available": false`
- **Fix:** Run `ollama pull nomic-embed-text`

## Step 7: Test the System

1. **Upload a PDF document** to a topic
   - The system will extract text and generate embeddings locally
   - No data leaves your machine

2. **Start a chat** and attach the resource
   - Ask questions about the document
   - The AI will retrieve relevant chunks using RAG

3. **Check performance**
   - First response may be slow (model loading)
   - Subsequent responses should be 2-5 seconds on CPU
   - With GPU: <1 second

## Performance Tuning

### Speed vs Quality Trade-offs

**Fastest (but lower quality):**
```bash
OLLAMA_CHAT_MODEL=phi:3b
```

**Best Balance:**
```bash
OLLAMA_CHAT_MODEL=mistral:7b
```

**Best Quality (but slower):**
```bash
OLLAMA_CHAT_MODEL=llama3:8b
```

### GPU Acceleration

Ollama automatically uses GPU if available:
- **NVIDIA:** Requires CUDA drivers
- **Apple Silicon:** Uses Metal automatically
- **AMD:** Requires ROCm on Linux

Check GPU usage:
```bash
# During a chat request
ollama ps
```

### Managing Disk Space

Models are stored in:
- **macOS:** `~/.ollama/models`
- **Linux:** `~/.ollama/models`
- **Windows:** `%USERPROFILE%\.ollama\models`

Remove unused models:
```bash
ollama rm model-name
```

## Switching Back to OpenAI (Optional)

If you want to temporarily use OpenAI:

1. Set environment variable:
   ```bash
   export LLM_PROVIDER=openai
   export OPENAI_API_KEY=your-key
   ```

2. Restart the Flask app

Both providers use the same code - switching is seamless!

## Troubleshooting

### Chat is very slow
- **Check:** Are you using CPU-only inference? First response loads the model (slow)
- **Fix:** Consider using a smaller model (`phi:3b`) or adding GPU

### "Connection refused" error
- **Check:** Is ollama serve running?
- **Fix:** Start it in a separate terminal

### Embeddings failing
- **Check:** Did you pull the embedding model?
- **Fix:** `ollama pull nomic-embed-text`

### Out of memory errors
- **Check:** RAM usage during inference
- **Fix:** Use a smaller model or close other applications

## Resource Usage

**Typical Usage (Mistral 7B):**
- **Model Size:** ~4.1GB on disk
- **RAM Usage:** 6-8GB during inference
- **CPU Inference:** 2-5 seconds per response
- **GPU Inference:** 0.5-1 second per response

**Embedding Model (Nomic Embed):**
- **Model Size:** ~274MB on disk
- **RAM Usage:** ~500MB during embedding generation

## Next Steps

Once you have local AI working, you can:
1. Disconnect from the internet and use Studymate fully offline
2. Upload sensitive documents without privacy concerns
3. Experiment with different models for different use cases
4. Contribute to the project by testing on different hardware

## Getting Help

- GitHub Issues: Report bugs or request features
- Ollama Docs: https://ollama.ai/docs
- Community: Share your hardware performance results!

---

**Remember:** Local AI is all about privacy and accessibility. No data leaves your machine, and it's completely free once set up!
