# Changelog

All notable changes to Studymate will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-01

### Added
- 🎉 **Initial public release**
- ✨ Local AI support via Ollama (privacy-first inference)
- 📄 PDF upload, text extraction, and automatic chunking
- 🔍 RAG (Retrieval Augmented Generation) implementation with semantic search
- 💬 Chat interface with conversation history
- 📚 Document-aware responses with source citations
- 🏥 Health check endpoint for system status
- 🔧 Provider abstraction layer supporting both Ollama and OpenAI
- 📝 Topic and subtopic organization
- 📖 Note-taking functionality
- 🔐 User authentication and authorization
- 📊 Vector embeddings stored in SQLite
- 🎨 VS Code-inspired dark theme UI
- 📱 Responsive web interface

### Features
- **LLM Providers**:
  - Ollama integration for local inference (Mistral 7B, Llama3, etc.)
  - OpenAI integration as optional cloud fallback
  - Easy provider switching via configuration
  
- **RAG Capabilities**:
  - Automatic PDF text extraction with page tracking
  - Smart chunking with overlap for context preservation
  - Semantic search using cosine similarity
  - Top-k retrieval with relevance scoring
  - Citation system referencing specific document excerpts

- **Study Organization**:
  - Hierarchical topic structure (topics and subtopics)
  - Note creation and management
  - Resource upload and categorization
  - Chat conversations linked to topics

### Documentation
- Comprehensive README with quick start guide
- Detailed setup instructions in `docs/local-ai-setup.md`
- Migration guide for future updates
- Contributing guidelines
- Code of conduct
- Security policy
- API documentation

### Developer Experience
- Clean provider abstraction pattern
- Type hints throughout codebase
- Comprehensive docstrings
- Health check for debugging
- Example environment configuration
- Issue templates for bug reports and feature requests

### Supported Platforms
- macOS (Intel and Apple Silicon)
- Linux (Ubuntu, Fedora, etc.)
- Windows (native and WSL2)

### Minimum Requirements
- Python 3.11+
- 8GB RAM (16GB recommended)
- 10GB free disk space
- Ollama 0.1.0+ (for local AI)

## [Unreleased]

### Planned
- Desktop application wrapper (PyWebView)
- ChromaDB integration for faster vector search
- Flashcard generation from documents
- Quiz/practice question generation
- Document summaries
- Export/import functionality
- Multi-language support
- Model management UI

---

## Release Notes

### v1.0.0 - "Privacy First"

This inaugural release focuses on providing a fully functional, privacy-first learning assistant that runs entirely on your computer. No cloud dependencies are required when using the default Ollama provider.

**Key Highlights:**
- 🔒 Complete data privacy with local AI
- 💰 Zero API costs with Ollama
- 📖 Smart document understanding via RAG
- 🎓 Built specifically for self-directed learners

**Breaking Changes:**
- N/A (initial release)

**Migration Notes:**
- N/A (initial release)

**Known Issues:**
- First chat response is slow (~5-10s) while model loads
- Embeddings from different providers are incompatible (can't switch without regenerating)
- No vector database yet (may be slow with >1000 document chunks)

**Contributors:**
- Fernando Guimaraes ([@fgmelofilho](https://github.com/fgmelofilho))

---

## Version History

- **1.0.0** (2026-03-01): Initial public release
- **0.1.0** (2026-02-01): Private development version

---

For detailed commit history, see the [GitHub commit log](https://github.com/yourusername/studymate/commits/main).
