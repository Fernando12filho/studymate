"""
Test script to verify OpenAI integration is working
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_config():
    """Test that OpenAI configuration is set up"""
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file based on .env.example and add your API key")
        return False
    
    if api_key == "your-openai-api-key-here":
        print("⚠️  OPENAI_API_KEY is still set to the default value")
        print("Please update .env with your actual OpenAI API key")
        return False
    
    print(f"✅ OPENAI_API_KEY is configured (starts with: {api_key[:8]}...)")
    
    # Test imports
    try:
        import openai
        import tiktoken
        print("✅ OpenAI and tiktoken libraries imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test token counting
    try:
        from app.ai_utils import count_tokens
        test_text = "Hello, this is a test message for token counting."
        tokens = count_tokens(test_text)
        print(f"✅ Token counting works: '{test_text}' = {tokens} tokens")
    except Exception as e:
        print(f"❌ Token counting error: {e}")
        return False
    
    print("\n✅ OpenAI integration is ready!")
    print("\nNext steps:")
    print("1. Test API connection with: python test_openai_api.py")
    print("2. Start building chat functionality")
    
    return True


if __name__ == "__main__":
    test_openai_config()
