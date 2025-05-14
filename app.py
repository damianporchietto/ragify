import os
import argparse
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import traceback

from rag_chain import load_rag_chain
from model_providers import list_available_providers

load_dotenv()  # Loads OPENAI_API_KEY and other vars from .env if present

# Read model configuration from environment variables
DEFAULT_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", None)
DEFAULT_EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", None)

app = Flask(__name__)
rag_chain = None  # Initialize lazily to avoid slow startup

# Simple HTML documentation for the API - Note the double curly braces for CSS
API_DOCS = """
<!DOCTYPE html>
<html>
<head>
    <title>Ragify - RAG Framework API</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        code {{ background: #f8f8f8; padding: 2px 5px; border-radius: 3px; }}
        pre {{ background: #f8f8f8; padding: 10px; border-radius: 5px; overflow: auto; }}
        .endpoint {{ margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .tester {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .tester textarea {{ width: 100%; height: 80px; padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 3px; }}
        .tester button {{ background-color: #2c3e50; color: white; border: none; padding: 10px 15px; border-radius: 3px; cursor: pointer; }}
        .tester button:hover {{ background-color: #1a2530; }}
        #result {{ margin-top: 20px; white-space: pre-wrap; }}
        .loading {{ display: none; margin-left: 10px; color: #666; }}
    </style>
</head>
<body>
    <h1>Ragify - RAG Framework API</h1>
    <p>API for knowledge-based question answering using Retrieval Augmented Generation.</p>
    
    <!-- Interactive test form -->
    <div class="tester">
        <h2>Test API</h2>
        <p>Enter a query and click "Send" to test the assistant:</p>
        <textarea id="query" placeholder="Example: What is the capital of France?"></textarea>
        <div>
            <button onclick="testApi()">Send Query</button>
            <span id="loading" class="loading">Processing query...</span>
        </div>
        <div id="result"></div>
    </div>
    
    <div class="endpoint">
        <h2>Ask a question</h2>
        <p><strong>Endpoint:</strong> <code>POST /ask</code></p>
        <p><strong>Description:</strong> Query information from the knowledge base.</p>
        <p><strong>Request Example:</strong></p>
        <pre>
{{
    "message": "What is the capital of France?"
}}
        </pre>
        <p><strong>Response Example:</strong></p>
        <pre>
{{
    "answer": "The capital of France is Paris. It is one of the world's major cities...",
    "sources": [
        {{
            "source": "/path/to/document.json",
            "snippet": "Excerpt from the source document..."
        }}
    ]
}}
        </pre>
    </div>
    
    <div class="endpoint">
        <h2>Check service status</h2>
        <p><strong>Endpoint:</strong> <code>GET /health</code></p>
        <p><strong>Description:</strong> Verify if the service is working correctly.</p>
    </div>
    
    <div class="endpoint">
        <h2>Current configuration</h2>
        <p><strong>Endpoint:</strong> <code>GET /config</code></p>
        <p><strong>Description:</strong> Shows the current model configuration.</p>
    </div>
    
    <div class="endpoint">
        <h2>Available providers</h2>
        <p><strong>Endpoint:</strong> <code>GET /providers</code></p>
        <p><strong>Description:</strong> Lists all available model providers.</p>
    </div>
    
    <h2>Current Configuration:</h2>
    <table>
        <tr>
            <th>Component</th>
            <th>Provider</th>
            <th>Model</th>
        </tr>
        <tr>
            <td>LLM</td>
            <td>{llm_provider}</td>
            <td>{llm_model}</td>
        </tr>
        <tr>
            <td>Embeddings</td>
            <td>{embedding_provider}</td>
            <td>{embedding_model}</td>
        </tr>
    </table>
    
    <script>
        function testApi() {{
            const query = document.getElementById('query').value.trim();
            if (!query) return;
            
            const resultDiv = document.getElementById('result');
            const loadingSpan = document.getElementById('loading');
            
            resultDiv.innerHTML = '';
            loadingSpan.style.display = 'inline';
            
            fetch('/ask', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{ message: query }})
            }})
            .then(response => response.json())
            .then(data => {{
                loadingSpan.style.display = 'none';
                
                // Format the result
                let result = '<h3>Response:</h3><div style="background: #f0f7ff; padding: 15px; border-radius: 5px; margin-bottom: 15px;">';
                result += data.answer.replace(/\\n/g, '<br>');
                result += '</div>';
                
                if (data.sources && data.sources.length > 0) {{
                    result += '<h3>Sources:</h3><ul>';
                    data.sources.forEach(source => {{
                        result += '<li>';
                        if (source.title) {{
                            result += '<strong>' + source.title + '</strong><br>';
                        }}
                        if (source.url) {{
                            result += '<a href="' + source.url + '" target="_blank">' + source.url + '</a><br>';
                        }}
                        if (source.snippet) {{
                            result += '<small>' + source.snippet + '...</small>';
                        }}
                        result += '</li>';
                    }});
                    result += '</ul>';
                }}
                
                resultDiv.innerHTML = result;
            }})
            .catch(error => {{
                loadingSpan.style.display = 'none';
                resultDiv.innerHTML = '<div style="color: red; background: #fff0f0; padding: 15px; border-radius: 5px;">Error: ' + error.message + '</div>';
            }});
        }}
        
        // Allow pressing Enter to submit
        document.getElementById('query').addEventListener('keydown', function(event) {{
            if (event.key === 'Enter') {{
                event.preventDefault();
                testApi();
            }}
        }});
    </script>
</body>
</html>
"""

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
    # Add current configuration to the documentation
    formatted_docs = API_DOCS.format(
        llm_provider=app.config['LLM_PROVIDER'],
        llm_model=app.config['LLM_MODEL'] or "Default",
        embedding_provider=app.config['EMBEDDING_PROVIDER'],
        embedding_model=app.config['EMBEDDING_MODEL'] or "Default"
    )
    return render_template_string(formatted_docs)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/config', methods=['GET'])
def config():
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
                        help='LLM provider (openai, ollama, huggingface)')
    parser.add_argument('--llm-model', type=str, default=DEFAULT_LLM_MODEL,
                        help='Specific LLM model to use')
    parser.add_argument('--embedding-provider', type=str, default=DEFAULT_EMBEDDING_PROVIDER,
                        help='Embedding provider (openai, ollama, huggingface)')
    parser.add_argument('--embedding-model', type=str, default=DEFAULT_EMBEDDING_MODEL,
                        help='Specific embedding model to use')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 5000)),
                        help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', default=bool(os.getenv('FLASK_DEBUG', False)),
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
    
    # Print configuration
    print(f"Starting server with:")
    print(f"  - LLM: {args.llm_provider} {args.llm_model or '(default model)'}")
    print(f"  - Embeddings: {args.embedding_provider} {args.embedding_model or '(default model)'}")
    
    app.run(host='0.0.0.0', port=args.port, debug=args.debug)