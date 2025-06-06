#!/usr/bin/env python3
"""
Simple test script to verify Google Gemini integration with RAGify.
Run this after setting up your GOOGLE_API_KEY to test the integration.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_import():
    """Test if Gemini dependencies can be imported."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        print("✅ Gemini dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Gemini dependencies: {e}")
        print("Install with: pip install langchain-google-genai")
        return False

def test_gemini_api_key():
    """Test if GOOGLE_API_KEY is set."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        print("✅ GOOGLE_API_KEY is set")
        return True
    else:
        print("❌ GOOGLE_API_KEY is not set")
        print("Get your API key from: https://aistudio.google.com/app/apikey")
        return False

def test_gemini_llm():
    """Test Gemini LLM initialization."""
    try:
        from model_providers import get_llm_model
        llm = get_llm_model(provider="gemini", model_name="gemini-1.5-flash")
        
        # Simple test query
        response = llm.invoke("What is 2+2?")
        print(f"✅ Gemini LLM test successful: {response.content[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Gemini LLM test failed: {e}")
        return False

def test_gemini_embeddings():
    """Test Gemini embeddings initialization."""
    try:
        from model_providers import get_embeddings_model
        embeddings = get_embeddings_model(provider="gemini", model_name="models/embedding-001")
        
        # Simple test embedding
        test_text = "This is a test sentence"
        embedding = embeddings.embed_query(test_text)
        print(f"✅ Gemini embeddings test successful: Generated {len(embedding)}-dimensional embedding")
        return True
    except Exception as e:
        print(f"❌ Gemini embeddings test failed: {e}")
        return False

def main():
    """Run all Gemini tests."""
    print("🧪 Testing Google Gemini Integration with RAGify")
    print("=" * 50)
    
    tests = [
        ("Import Dependencies", test_gemini_import),
        ("API Key Setup", test_gemini_api_key),
        ("LLM Functionality", test_gemini_llm),
        ("Embeddings Functionality", test_gemini_embeddings),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 All tests passed! Gemini integration is ready to use.")
        print("\nTo use Gemini with RAGify:")
        print("  python app.py --llm-provider gemini --llm-model gemini-1.5-flash")
    else:
        print("\n⚠️  Some tests failed. Please check the requirements above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 