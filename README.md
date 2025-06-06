# RAGify - A Modern RAG Framework

[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

A comprehensive **Retrieval-Augmented Generation (RAG)** framework for building intelligent knowledge-based Q&A systems. Built with **Flask**, **LangChain**, and featuring a modern web interface.

## 🚀 Features

- **🌐 Web Chat Interface**: Beautiful, responsive chat client with real-time interactions
- **🔧 Flexible Configuration**: YAML-based configuration with environment variable overrides
- **🤖 Multi-Provider Support**: OpenAI, Ollama, and HuggingFace model providers
- **📄 Document Processing**: Support for JSON, TXT, MD, and PDF files
- **🔍 Vector Search**: FAISS-powered semantic search
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
├── storage/               # FAISS vector database (auto-generated)
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
LLM_PROVIDER=openai              # openai, ollama, huggingface
LLM_MODEL=gpt-4o-mini
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large

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

### Ollama (Local Models)
```bash
# Install Ollama first: https://ollama.ai
# Pull required models
ollama pull mistral
ollama pull nomic-embed-text

# Run with Ollama
python app.py --llm-provider ollama --llm-model mistral --embedding-provider ollama --embedding-model nomic-embed-text
```

### HuggingFace
```bash
# Install HuggingFace dependencies
pip install langchain-huggingface transformers torch sentence-transformers accelerate

# Run with HuggingFace
python app.py --llm-provider huggingface --llm-model google/flan-t5-xxl
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
python ingest.py --provider ollama --model nomic-embed-text
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
  search_type: "similarity"     # similarity, mmr
  top_k_results: 4             # Number of retrieved documents
```

### Document Processing

Adjust chunk settings:

```yaml
document_processing:
  chunk_size: 1000            # Characters per chunk
  chunk_overlap: 200          # Overlap between chunks
```

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
- [FAISS](https://github.com/facebookresearch/faiss) for efficient vector similarity search
- [Flask](https://flask.palletsprojects.com/) for the web framework
- Modern CSS and JavaScript for the responsive chat interface

## 📬 Support

- Create an [issue](https://github.com/your-repo/ragify/issues) for bug reports
- Start a [discussion](https://github.com/your-repo/ragify/discussions) for questions
- Check the [documentation](http://localhost:5000/) when running the server

---

**RAGify** - Making knowledge accessible through intelligent conversation. 🤖✨