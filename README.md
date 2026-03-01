# 📚 Studymate

**Privacy-first, AI-powered learning assistant that runs entirely on your computer.**

Studymate is an open-source educational platform that helps students organize resources, take notes, and engage with learning materials using **local AI** - no cloud dependencies, no API costs, complete data ownership.

## ✨ Features

- 📝 **Note Taking** - Organize study notes by topic and subtopic
- 📄 **PDF Management** - Upload and manage learning resources
- 🤖 **Local AI Chat** - Ask questions about your materials using Ollama
- 🔍 **RAG (Retrieval Augmented Generation)** - AI retrieves relevant document sections to answer questions
- 📚 **Source Citations** - AI references specific document excerpts
- 💰 **Zero Cost** - No API fees, runs entirely on your device
- 🔒 **Complete Privacy** - Your data never leaves your computer
- 📡 **Offline Ready** - Works without internet after initial setup

## 🎯 Philosophy

AI in education should be:
- **Accessible** - Works on regular laptops, not just high-end hardware
- **Private** - Students control their own data
- **Transparent** - Open source, verifiable, modifiable
- **Supportive** - Helps understanding, doesn't replace learning

Studymate is built for self-directed learners who want AI assistance **without** sacrificing privacy or paying monthly subscriptions.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space
- macOS, Linux, or Windows

### 1. Install Ollama

```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh

# Or download from: https://ollama.ai
```

### 2. Download AI Models

```bash
# Start Ollama service
ollama serve

# In a new terminal, pull models
ollama pull mistral:7b
ollama pull nomic-embed-text
```

### 3. Setup Studymate

```bash
# Clone repository
git clone [your-repo-url]
cd studymate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional - uses local AI by default)
echo "LLM_PROVIDER=ollama" > .env

# Run database migrations
flask db upgrade

# Start application
python manage.py
```

### 4. Verify Setup

```bash
# Check health status
curl http://localhost:5000/api/health

# Should return: "status": "healthy"
```

Visit `http://localhost:5000` and create an account!

## 📖 Usage

1. **Create a Topic** - e.g., "Machine Learning 101"
2. **Upload Resources** - Add PDF textbooks, papers, notes
3. **Chat with AI** - Ask questions, attach relevant resources
4. **Get Cited Answers** - AI retrieves and references specific sections

### Example Workflow

```
1. Upload "Introduction to Algorithms" PDF
   → System extracts text, generates embeddings locally
   
2. Start chat: "Explain how quicksort works"
   → AI retrieves relevant book sections
   → Provides answer with citations: "According to Excerpt 1 (page 170)..."
   
3. Follow-up: "What's the time complexity?"
   → AI maintains conversation context
   → References multiple sections if needed
```

## 🛠️ Configuration

Environment variables (`.env` file):

```bash
# LLM Provider (default: ollama)
LLM_PROVIDER=ollama

# Ollama Settings
OLLAMA_CHAT_MODEL=mistral:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434

# Optional: OpenAI Fallback
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-key-here
```

### Recommended Models

**For Speed (CPU-friendly):**
- Chat: `phi:3b`
- Embedding: `nomic-embed-text`

**For Quality:**
- Chat: `llama3:8b`
- Embedding: `nomic-embed-text`

**Best Balance:**
- Chat: `mistral:7b` ⭐ (default)
- Embedding: `nomic-embed-text` ⭐ (default)

## 🏗️ Architecture

```
Studymate
├── Flask Web App (Backend)
│   ├── User Auth & Sessions
│   ├── Topic/Resource Management
│   └── Chat & RAG Engine
├── LLM Provider Abstraction
│   ├── OllamaProvider (local)
│   └── OpenAIProvider (optional)
├── RAG Pipeline
│   ├── PDF Text Extraction
│   ├── Chunking & Embedding
│   └── Semantic Search
└── SQLite Database
    ├── User Data
    ├── Notes & Resources
    └── Document Chunks + Embeddings
```

## 📚 Documentation

- **[Local AI Setup Guide](docs/local-ai-setup.md)** - Complete setup instructions
- **[Migration Guide](docs/migration-guide.md)** - Upgrade from older versions
- **[Project Status](docs/project-status.md)** - Roadmap and current features

## 🤝 Contributing

Contributions welcome! Areas of interest:

- 🧪 Testing on different hardware configurations
- 🎨 UI/UX improvements
- 📝 Documentation enhancements
- 🔬 Model experimentation
- 🐛 Bug fixes

**How to contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🎓 Use Cases

- **Self-Directed Learners** - Study independently with AI assistance
- **University Students** - Organize course materials, get study help
- **Researchers** - Manage papers, query literature
- **Privacy-Conscious Users** - Keep sensitive academic data local
- **Offline Learners** - Study without reliable internet access

## 🔧 Troubleshooting

**Chat responses are slow:**
- Expected: 2-5 seconds on CPU (first response loads model)
- Try smaller model: `ollama pull phi:3b`
- Check GPU is being used: `ollama ps` during inference

**"Connection refused" error:**
- Ensure Ollama is running: `ollama serve`
- Check health: `curl http://localhost:5000/api/health`

**PDF embedding fails:**
- Verify embedding model: `ollama list` should show `nomic-embed-text`
- Pull if missing: `ollama pull nomic-embed-text`

**More help:** See [docs/local-ai-setup.md](docs/local-ai-setup.md)

## 🤝 Contributing

Contributions are welcome! We'd love your help making Studymate better.

**Ways to contribute:**
- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🧪 Add tests
- 🎨 Enhance UI/UX
- 🔬 Test on different hardware

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

**Areas we need help:**
- Cross-platform testing (Windows, Linux, macOS)
- Performance benchmarking
- Model comparison studies
- Unit and integration tests
- Advanced RAG features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**TL;DR:** You can freely use, modify, and distribute this software, even for commercial purposes, as long as you include the original copyright and license notice.

## 🛡️ Security

See [SECURITY.md](SECURITY.md) for our security policy and how to report vulnerabilities responsibly.

## 📧 Contact

- **GitHub**: [@fgmelofilho](https://github.com/fgmelofilho) *(update with your username)*
- **LinkedIn**: [Fernando Guimaraes](https://linkedin.com/in/yourprofile) *(update with your profile)*
- **Email**: fgmelofilho@gmail.com

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM runtime
- [Mistral AI](https://mistral.ai) - Open-source language models
- [Nomic AI](https://nomic.ai) - Embedding models
- Flask community - Web framework

## 🌟 Project Goals

1. ✅ **Phase 1:** Local AI integration (Complete!)
2. 🚧 **Phase 2:** Desktop application with PyWebView
3. 🔮 **Phase 3:** Enhanced study tools (flashcards, quizzes, summaries)

## 📣 Stay Updated

This is an active "build in public" project:
- Follow development on [LinkedIn](#) (link TBD)
- Star ⭐ the repo for updates
- Join discussions in Issues

---

**Built with ❤️ for learners who value privacy and accessibility.**

*"Technology doesn't only bring comfort and convenience — it brings people closer to knowledge."*
