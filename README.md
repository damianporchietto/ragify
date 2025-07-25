# RAGify - A Modern RAG Framework

[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

A comprehensive **Retrieval-Augmented Generation (RAG)** framework for building intelligent knowledge-based Q&A systems. Built with **Flask**, **LangChain**, and featuring a modern web interface.

## 🚀 Features

- **🌐 Web Chat Interface**: Beautiful, responsive chat client with real-time interactions
- **🔧 Flexible Configuration**: YAML-based configuration with environment variable overrides
- **🤖 Multi-Provider Support**: OpenAI and Vertex AI (Google Cloud) model providers
- **📄 Document Processing**: Support for JSON, TXT, MD, and PDF files
- **🔍 Vector Search**: Qdrant-powered semantic search
- **⚡ RESTful API**: Complete API with health checks, configuration endpoints
- **🧪 Testing Suite**: Comprehensive testing tools for model evaluation
- **📱 Responsive Design**: Mobile-friendly chat interface
- **⚙️ Easy Setup**: Automated environment setup scripts

## 📁 Project Structure

```
ragify/
├── app.py                      # Main Flask application with API endpoints
├── rag_chain.py               # RAG pipeline implementation
├── ingest.py                  # Document ingestion and vector database creation
├── model_providers.py         # Multi-provider model management
├── config_manager.py          # Configuration management system
├── config.yaml               # Main configuration file
├── setup_env.sh              # Automated environment setup script
├── requirements.txt          # Python dependencies
├── client/                   # Web chat interface
│   ├── index.html           # Chat client HTML
│   ├── script.js            # Client-side JavaScript
│   └── styles.css           # Responsive CSS styling
├── templates/               # Flask templates
│   └── api_docs.html       # API documentation template
├── docs/                   # Knowledge base documents
│   ├── GEOGRAPHY/          # Geography-related documents
│   ├── RECIPES/           # Recipe and cooking documents
│   └── TECH/              # Technology-related documents
├── qdrant_data/           # Qdrant vector database storage (auto-generated)
├── test_models.py         # Model testing utilities
├── test_multiple_models.sh # Batch testing script
└── dotenv                 # Environment variables template
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ragify

# Run the automated setup script
chmod +x setup_env.sh
./setup_env.sh
```

The script will:
- Create a Python virtual environment
- Install all dependencies
- Set up environment variables
- Offer provider-specific installations

### Option 2: Manual Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp dotenv .env
# Edit .env file with your API keys

# 4. Ingest documents to create vector database
python ingest.py

# 5. Start the server
python app.py
```

## 💬 Using the Chat Interface

Once the server is running, access the chat interface at:

**http://localhost:5000/chat**

Features:
- Real-time chat with the RAG system
- **Conversation memory** - remembers last 5 interactions for context
- **Markdown support** for rich text formatting in responses
- **Syntax highlighting** for code blocks
- Source document references with previews
- Typing indicators and status monitoring
- Message history persistence
- Responsive design for mobile and desktop
- Settings panel for customization

## 🔧 Configuration

RAGify uses a comprehensive YAML-based configuration system with environment variable overrides.

### Configuration File (`config.yaml`)

```yaml
# Server settings
server:
  port: 5000
  debug: true
  host: "0.0.0.0"

# Model configuration
models:
  defaults:
    llm_provider: "openai"
    llm_model: null  # Uses provider default
    embedding_provider: "openai"
    embedding_model: null  # Uses provider default
    temperature: 0

# Document processing
document_processing:
  chunk_size: 1000
  chunk_overlap: 200

# And much more...
```

### Environment Variables

Key environment variables for configuration:

```bash
# API Keys
OPENAI_API_KEY=sk-...

# Provider Selection
LLM_PROVIDER=openai              # openai, vertexai
LLM_MODEL=gpt-4o-mini
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large

# Google Cloud / Vertex AI (if using vertexai provider)
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
VERTEX_PROJECT=your-gcp-project-id
VERTEX_REGION=us-central1
VERTEX_LLM_MODEL=gemini-pro
VERTEX_EMBEDDING_MODEL=textembedding-gecko@latest

# Server Configuration
PORT=5000
FLASK_DEBUG=true
```

## 🤖 Model Providers

### OpenAI (Default)
```bash
# Set your API key
export OPENAI_API_KEY=sk-...

# Run with OpenAI (default)
python app.py --llm-provider openai --llm-model gpt-4o-mini
```

### Vertex AI (Google Cloud)
```bash
# Set up Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Run with Vertex AI
python app.py --llm-provider vertexai --llm-model gemini-pro --embedding-provider vertexai --embedding-model textembedding-gecko@latest

# Additional configuration options
python app.py --llm-provider vertexai --vertex-project your-gcp-project-id --vertex-region us-central1
```

## 🌐 API Endpoints

The Flask application provides a comprehensive RESTful API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/chat` | GET | Web chat interface |
| `/health` | GET | Health check |
| `/config` | GET | Current configuration |
| `/providers` | GET | Available model providers |
| `/ask` | POST | Query the knowledge base |

### API Example

```bash
# Query the knowledge base
curl -X POST http://localhost:5000/ask \
     -H 'Content-Type: application/json' \
     -d '{"message": "What is the capital of France?"}'
```

**Response:**
```json
{
  "answer": "The capital of France is Paris...",
  "sources": [
    {
      "source": "docs/GEOGRAPHY/france.json",
      "title": "France Information",
      "url": "https://example.com/france",
      "snippet": "France is a country located in Western Europe..."
    }
  ]
}
```

## 📚 Knowledge Base Management

### Adding Documents

RAGify supports multiple document formats:

```bash
# Supported formats
docs/
├── GEOGRAPHY/
│   ├── countries.json    # Structured JSON data
│   ├── cities.txt       # Plain text
│   └── atlas.pdf        # PDF documents
├── RECIPES/
│   └── cooking.md       # Markdown files
```

### Document Processing

After adding documents, rebuild the vector database:

```bash
# Rebuild with current configuration
python ingest.py

# Rebuild with specific embedding provider
python ingest.py --provider vertexai --model textembedding-gecko@latest
```

## 🧪 Testing

### Testing Individual Models

```bash
python test_models.py --model-name "test_configuration"
```

### Batch Testing Multiple Configurations

```bash
./test_multiple_models.sh
```

### Custom Test Questions

Configure test questions in `config.yaml`:

```yaml
testing:
  default_questions:
    - "What is the capital of France?"
    - "How do I make sourdough bread?"
    - "What equipment do I need for a podcast?"
```

## 🔧 Advanced Configuration

### Custom Prompt Templates

Modify the RAG prompt in `config.yaml`:

```yaml
prompts:
  rag_template: |
    You're a smart, relaxed assistant in your late 20s. You sound human—like someone who knows their stuff...
    
    Context:
    {context}
    
    User Question:
    {query}
    
    Answer:
```

### Retrieval Settings

Fine-tune retrieval behavior:

```yaml
retrieval:
  search_type: "mmr"           # "similarity" or "mmr" (Maximal Marginal Relevance)
  top_k_results: 2             # Number of retrieved documents (reduced for better precision)
  mmr_diversity_score: 0.5     # Balance between relevance (0.0) and diversity (1.0)
```

**Search Types:**
- **similarity**: Pure semantic similarity search
- **mmr**: Maximal Marginal Relevance - balances relevance with diversity to reduce redundant results

**Optimization Tips:**
- Lower `top_k_results` (2-3) for better precision and less irrelevant context
- Use `mmr` search type to avoid redundant similar documents
- Adjust `mmr_diversity_score`: closer to 0.0 for relevance, closer to 1.0 for diversity

### Document Processing

Adjust chunk settings:

```yaml
document_processing:
  chunk_size: 1000            # Characters per chunk
  chunk_overlap: 200          # Overlap between chunks
```

### Conversation History

Configure chat memory settings:

```yaml
chat:
  history_length: 5           # Number of previous interactions to remember
  max_context_tokens: 2000    # Maximum tokens for chat history context
```

The system automatically remembers the last 5 user-assistant interactions and uses them as context for follow-up questions. This enables:
- Natural conversation flow
- Follow-up questions without repeating context
- Reference to previous answers
- Contextual clarifications

**Query Rewriting for Better Retrieval:**
The system includes intelligent query rewriting that incorporates conversation history into document retrieval. When you ask a follow-up question like "Can you explain that in more detail?", the system rewrites it to include context from previous exchanges, ensuring the vector database retrieves relevant documents for the complete context, not just the isolated question.

## 🚀 Deployment

### Development
```bash
python app.py --debug
```

### Production
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using Docker (create Dockerfile)
docker build -t ragify .
docker run -p 5000:5000 ragify
```

## 🤝 Contributing

RAGify is open source under the BSD-3-Clause license. Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) for RAG pipeline management
- [Qdrant](https://qdrant.tech/) for efficient vector similarity search and persistence
- [Flask](https://flask.palletsprojects.com/) for the web framework
- Modern CSS and JavaScript for the responsive chat interface
- [Flask-Limiter](https://flask-limiter.readthedocs.io/) for API rate limiting

## 📬 Support

- Create an [issue](https://github.com/damianporchietto/ragify/issues) for bug reports
- Start a [discussion](https://github.com/damianporchietto/ragify/discussions) for questions
- Check the [documentation](http://localhost:5000/) when running the server

---

**RAGify** - Making knowledge accessible through intelligent conversation. 🤖✨