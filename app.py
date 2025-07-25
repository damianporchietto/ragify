import os
import argparse
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
from dotenv import load_dotenv
import traceback
from pathlib import Path

from rag_chain import load_rag_chain
from model_providers import list_available_providers
from config_manager import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Security configuration
app.config['MAX_CONTENT_LENGTH'] = config.get('server.max_content_length', 16 * 1024 * 1024)  # 16MB

# Initialize rate limiter if enabled
rate_limit_config = config.get('server.rate_limit', {})
if rate_limit_config.get('enabled', True):
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{rate_limit_config.get('requests_per_minute', 1)} per minute"]
    )
else:
    limiter = None

rag_chain = None  # Initialize lazily to avoid slow startup

def validate_request_data(data: Dict[str, Any]) -> Optional[str]:
    """Validate incoming request data."""
    if not isinstance(data, dict):
        return "Request must be a JSON object"
    
    message = data.get('message') or data.get('question')
    if not message:
        return "Request must contain 'message' or 'question' field"
    
    if not isinstance(message, str):
        return "Message must be a string"
    
    if len(message.strip()) == 0:
        return "Message cannot be empty"
    
    if len(message) > 10000:  # 10KB limit
        return "Message too long (max 10,000 characters)"
    
    return None

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
@limiter.limit("10 per minute") if limiter else lambda f: f
def ask():
    """Process a question using the RAG system."""
    try:
        # Validate content type
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        # Get and validate request data
        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({'error': 'Invalid JSON payload'}), 400
        
        # Validate request data
        validation_error = validate_request_data(data)
        if validation_error:
            return jsonify({'error': validation_error}), 400
        
        question = data.get('message') or data.get('question')
        logger.info(f"Processing question: {question[:100]}...")
        
        # Lazy load RAG chain on first request
        chain = get_rag_chain()
        
        # Process the query
        result = chain(question)
        
        answer = result.get('result') or result.get('answer')
        if not answer:
            logger.warning("Empty answer received from RAG chain")
            return jsonify({'error': 'Unable to generate answer'}), 500
        
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
        
        logger.info(f"Successfully processed question with {len(sources)} sources")
        return jsonify({
            'answer': answer,
            'sources': sources
        })
    
    except RequestEntityTooLarge:
        logger.warning("Request entity too large")
        return jsonify({'error': 'Request too large'}), 413
    except BadRequest as e:
        logger.warning(f"Bad request: {str(e)}")
        return jsonify({'error': 'Invalid request format'}), 400
    except Exception as exc:
        logger.error(f"Error processing query: {str(exc)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500

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