import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "the-dev-should-change-this")

    # Ensure proper SQLite URI format for absolute paths
    _db_path = os.path.join(INSTANCE_DIR, 'contacts.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{_db_path}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(INSTANCE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf'}

    # ============================================================================
    # LLM PROVIDER CONFIGURATION
    # ============================================================================
    # Choose provider: 'ollama' (local, privacy-first) or 'openai' (cloud)
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
    
    # Ollama Configuration (local inference)
    OLLAMA_CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "mistral:7b")
    OLLAMA_EMBEDDING_MODEL = os.environ.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # OpenAI Configuration (cloud inference, fallback)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_MAX_TOKENS = int(os.environ.get("OPENAI_MAX_TOKENS", "4000"))
    OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0.7"))
