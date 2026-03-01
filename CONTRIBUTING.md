# Contributing to Studymate

Thank you for your interest in contributing to Studymate! This document provides guidelines for contributing to the project.

## 🎯 Project Vision

Studymate aims to make AI-powered learning accessible, private, and free for everyone. When contributing, please keep these principles in mind:

- **Privacy-first**: User data should stay on their device
- **Accessibility**: Should work on regular consumer hardware
- **Open & Transparent**: Code should be readable and well-documented
- **Educational Focus**: Features should support learning, not replace it

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Git
- Ollama (for local AI)
- 8GB+ RAM

### Setup Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/studymate.git
   cd studymate
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama and Models**
   ```bash
   # Install Ollama
   curl https://ollama.ai/install.sh | sh
   
   # Start Ollama
   ollama serve
   
   # Pull models (in another terminal)
   ollama pull mistral:7b
   ollama pull nomic-embed-text
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

6. **Run Database Migrations**
   ```bash
   flask db upgrade
   ```

7. **Start Development Server**
   ```bash
   python manage.py
   ```

## 🔄 Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code improvements

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Test basic functionality
   curl http://localhost:5000/api/health
   
   # Test your specific feature
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add description of your feature"
   ```
   
   **Commit message format:**
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `refactor:` - Code refactoring
   - `test:` - Adding tests
   - `chore:` - Maintenance tasks

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub

## 📝 Code Style Guidelines

### Python

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small
- Use meaningful variable names

**Example:**
```python
def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
        
    Returns:
        Similarity score between 0 and 1
    """
    # Implementation here
    pass
```

### Frontend (HTML/CSS/JS)

- Use semantic HTML
- Keep CSS organized by component
- Vanilla JavaScript preferred (no heavy frameworks)
- Comment complex UI logic

## 🐛 Reporting Bugs

**Before submitting:**
1. Check if the issue already exists
2. Try to reproduce with latest code
3. Test with health check: `/api/health`

**When submitting:**
- Use the bug report template
- Include steps to reproduce
- Provide error messages/logs
- Mention your environment:
  - OS and version
  - Python version
  - Hardware specs (RAM, CPU/GPU)
  - Ollama version
  - Model being used

## 💡 Suggesting Features

We welcome feature suggestions! Please:

1. **Check existing issues** - Your idea might already be proposed
2. **Explain the problem** - What need does this address?
3. **Describe the solution** - How would it work?
4. **Consider alternatives** - Any other approaches?
5. **Think about scope** - Does it fit the project vision?

**Prioritized areas:**
- Improved RAG quality (better chunking, ranking)
- Study tools (flashcards, quizzes, summaries)
- Model management UI
- Performance optimizations
- Cross-platform desktop app (Phase 2)
- Better citation system
- Multi-language support

## 🧪 Testing

Currently, testing is manual. We'd love contributions to add:
- Unit tests (pytest)
- Integration tests
- RAG quality benchmarks
- Performance benchmarks

## 📚 Documentation

Good documentation is crucial! Help by:
- Improving README clarity
- Adding code comments
- Writing tutorials
- Creating video guides
- Translating docs
- Documenting edge cases

## 🤝 Community Guidelines

- **Be respectful** - Everyone is learning
- **Be patient** - Maintainers are volunteers
- **Be constructive** - Focus on solutions
- **Be inclusive** - Welcome all backgrounds
- **Give credit** - Acknowledge others' work

## 📊 Areas We Need Help

### High Priority
- [ ] Unit and integration tests
- [ ] Performance benchmarking
- [ ] Cross-platform testing (Windows, Linux, macOS)
- [ ] Model comparison studies
- [ ] UI/UX improvements

### Medium Priority
- [ ] Advanced RAG features (ChromaDB, re-ranking)
- [ ] Flashcard generation
- [ ] Quiz/practice problems
- [ ] PDF annotation/highlighting
- [ ] Export/import functionality

### Future
- [ ] Desktop app packaging (PyWebView)
- [ ] Mobile version considerations
- [ ] Cloud sync (optional, encrypted)
- [ ] Fine-tuning support
- [ ] Plugin system

## ❓ Questions?

- **General questions**: Open a Discussion on GitHub
- **Bug reports**: Open an Issue
- **Security issues**: Email directly (see SECURITY.md)
- **Feature ideas**: Open an Issue with [Feature Request] tag

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make education more accessible!** 🎓
