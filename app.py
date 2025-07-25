import os
import argparse
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
import traceback
from pathlib import Path

from rag_chain import load_rag_chain
from model_providers import list_available_providers
from config_manager import config

load_dotenv()  # Loads OPENAI_API_KEY and other vars from .env if present

# Read model configuration from config manager
DEFAULT_LLM_PROVIDER = config.get_default_llm_provider()
DEFAULT_LLM_MODEL = config.get_default_llm_model()
DEFAULT_EMBEDDING_PROVIDER = config.get_default_embedding_provider()
DEFAULT_EMBEDDING_MODEL = config.get_default_embedding_model()

# Configure Flask to serve static files from client folder
app = Flask(__name__, 
            static_folder='client',
            static_url_path='/client')
rag_chain = None  # Initialize lazily to avoid slow startup

def get_rag_chain():
    global rag_chain
    if rag_chain is None:
        # Initialize with configured providers and models
        rag_chain = load_rag_chain(
            llm_provider=app.config['LLM_PROVIDER'],
            llm_model=app.config['LLM_MODEL'],
            embedding_provider=app.config['EMBEDDING_PROVIDER'],
            embedding_model=app.config['EMBEDDING_MODEL']
        )
    return rag_chain

@app.route('/', methods=['GET'])
def index():
    # Load API documentation from config
    api_config = config.get('api_docs', {})
    
    return render_template('api_docs.html',
        title=api_config.get('title', 'Ragify - RAG Framework API'),
        description=api_config.get('description', 'API for knowledge-based question answering using Retrieval Augmented Generation.'),
        llm_provider=app.config['LLM_PROVIDER'],
        llm_model=app.config['LLM_MODEL'] or "Default",
        embedding_provider=app.config['EMBEDDING_PROVIDER'],
        embedding_model=app.config['EMBEDDING_MODEL'] or "Default"
    )

@app.route('/chat', methods=['GET'])
def chat_client():
    """Serve the chat client interface."""
    return send_from_directory('client', 'index.html')

@app.route('/client/<path:filename>')
def client_files(filename):
    """Serve static files from the client directory."""
    return send_from_directory('client', filename)

@app.route('/health', methods=['GET'])
def health():
    try:
        # Try to initialize the RAG chain to ensure everything is working
        global rag_chain
        if rag_chain is None:
            rag_chain = load_rag_chain(
                llm_provider=app.config['LLM_PROVIDER'],
                llm_model=app.config['LLM_MODEL'],
                embedding_provider=app.config['EMBEDDING_PROVIDER'],
                embedding_model=app.config['EMBEDDING_MODEL']
            )
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/config', methods=['GET'])
def get_config():
    return jsonify({
        'llm': {
            'provider': app.config['LLM_PROVIDER'],
            'model': app.config['LLM_MODEL']
        },
        'embeddings': {
            'provider': app.config['EMBEDDING_PROVIDER'],
            'model': app.config['EMBEDDING_MODEL']
        }
    })

@app.route('/providers', methods=['GET'])
def providers():
    return jsonify(list_available_providers())

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json(force=True, silent=True) or {}
    question = data.get('message') or data.get('question')
    
    if not question:
        return jsonify({'error': 'JSON payload must contain "message" or "question"'}), 400
    
    try:
        # Lazy load RAG chain on first request
        chain = get_rag_chain()
        
        # Process the query
        result = chain(question)
        
        answer = result.get('result') or result.get('answer')
        sources = []
        
        # Extract source information if available
        if 'source_documents' in result and result['source_documents']:
            sources = [
                {
                    'source': d.metadata.get('source', ''),
                    'title': d.metadata.get('title', ''),
                    'url': d.metadata.get('url', ''),
                    'snippet': d.page_content[:200] + '...' if len(d.page_content) > 200 else d.page_content
                }
                for d in result.get('source_documents', [])
            ]
        
        return jsonify({
            'answer': answer, 
            'sources': sources
        })
    
    except Exception as exc:
        app.logger.error(f"Error processing query: {str(exc)}\n{traceback.format_exc()}")
        return jsonify({'error': str(exc)}), 500

def parse_args():
    parser = argparse.ArgumentParser(description='Run the RAG Flask API with configurable models')
    parser.add_argument('--llm-provider', type=str, default=DEFAULT_LLM_PROVIDER,
                        help='LLM provider (openai, vertexai)')
    parser.add_argument('--llm-model', type=str, default=DEFAULT_LLM_MODEL,
                        help='Specific LLM model to use')
    parser.add_argument('--embedding-provider', type=str, default=DEFAULT_EMBEDDING_PROVIDER,
                        help='Embedding provider (openai, vertexai)')
    parser.add_argument('--embedding-model', type=str, default=DEFAULT_EMBEDDING_MODEL,
                        help='Specific embedding model to use')
    parser.add_argument('--port', type=int, default=config.get_port(),
                        help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', default=config.get_debug(),
                        help='Run in debug mode')
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    # Configure the app with model settings
    app.config.update({
        'LLM_PROVIDER': args.llm_provider,
        'LLM_MODEL': args.llm_model,
        'EMBEDDING_PROVIDER': args.embedding_provider,
        'EMBEDDING_MODEL': args.embedding_model
    })
    
    # Print configuration and available routes
    print(f"Starting server with:")
    print(f"  - LLM: {args.llm_provider} {args.llm_model or '(default model)'}")
    print(f"  - Embeddings: {args.embedding_provider} {args.embedding_model or '(default model)'}")
    print(f"\nAvailable endpoints:")
    print(f"  - API Documentation: http://localhost:{args.port}/")
    print(f"  - Chat Client: http://localhost:{args.port}/chat")
    print(f"  - Health Check: http://localhost:{args.port}/health")
    print(f"  - Configuration: http://localhost:{args.port}/config")
    
    app.run(host=config.get_host(), port=args.port, debug=args.debug)