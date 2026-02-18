from flask import Blueprint, render_template, request, jsonify, current_app
from .extensions import db
from .models import User

bp = Blueprint("main", __name__)

@bp.get("/dev/seed")
def dev_seed():
    c = User(name="TPM", email="fgmelofilho@gmail.com", phone="000-000-0000")
    db.session.add(c)
    db.session.commit()
    return f"Inserted contact id={c.id}"


@bp.get("/")
def home():
    return render_template("index.html")


@bp.get("/api/health")
def health_check():
    """Health check endpoint to verify LLM provider availability"""
    provider_type = current_app.config.get('LLM_PROVIDER', 'ollama')
    
    health_status = {
        'status': 'unknown',
        'provider': provider_type,
        'details': {}
    }
    
    try:
        if provider_type == 'ollama':
            # Check Ollama connection
            import ollama
            base_url = current_app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            chat_model = current_app.config.get('OLLAMA_CHAT_MODEL', 'mistral:7b')
            embedding_model = current_app.config.get('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')
            
            try:
                client = ollama.Client(host=base_url)
                # List available models
                models = client.list()
                model_names = [m['name'] for m in models.get('models', [])]
                
                # Check if required models are available
                chat_available = any(chat_model in name for name in model_names)
                embed_available = any(embedding_model in name for name in model_names)
                
                health_status['status'] = 'healthy' if (chat_available and embed_available) else 'degraded'
                health_status['details'] = {
                    'ollama_running': True,
                    'base_url': base_url,
                    'chat_model': chat_model,
                    'chat_model_available': chat_available,
                    'embedding_model': embedding_model,
                    'embedding_model_available': embed_available,
                    'available_models': model_names
                }
                
                if not chat_available:
                    health_status['details']['warning'] = f"Chat model '{chat_model}' not found. Run: ollama pull {chat_model}"
                if not embed_available:
                    health_status['details']['warning'] = f"Embedding model '{embedding_model}' not found. Run: ollama pull {embedding_model}"
                    
            except Exception as ollama_error:
                health_status['status'] = 'unhealthy'
                health_status['details'] = {
                    'ollama_running': False,
                    'error': str(ollama_error),
                    'suggestion': 'Is Ollama running? Try: ollama serve'
                }
        
        elif provider_type == 'openai':
            # Check OpenAI configuration
            api_key = current_app.config.get('OPENAI_API_KEY')
            model = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')
            
            if api_key:
                health_status['status'] = 'healthy'
                health_status['details'] = {
                    'api_key_configured': True,
                    'model': model
                }
            else:
                health_status['status'] = 'unhealthy'
                health_status['details'] = {
                    'api_key_configured': False,
                    'error': 'OPENAI_API_KEY not set'
                }
        
        else:
            health_status['status'] = 'unhealthy'
            health_status['details'] = {
                'error': f"Unknown provider type: {provider_type}"
            }
    
    except ImportError as e:
        health_status['status'] = 'unhealthy'
        health_status['details'] = {
            'error': f"Missing dependency: {str(e)}",
            'suggestion': 'Run: pip install -r requirements.txt'
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['details'] = {
            'error': str(e)
        }
    
    return jsonify(health_status)
