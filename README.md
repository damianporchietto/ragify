# Ragify - A RAG Framework

Retrieval-Augmented Generation (RAG) service for creating knowledge-based Q&A systems. Built with **Flask** and **LangChain**.

## Project Structure

```
ragify/
├── app.py               # Flask API (GET /, GET /health, GET /config, GET /providers, POST /ask)
├── rag_chain.py         # RAG Pipeline (embeddings + vector DB + LLM)
├── ingest.py            # Vector database creation from JSON files in ./docs
├── model_providers.py   # Module for managing different model providers (OpenAI, Ollama, etc.)
├── setup_env.sh         # Script to set up virtual environment and install dependencies
├── test_models.py       # Script to test individual models
├── test_multiple_models.sh # Script to test multiple model configurations
├── requirements.txt     # Python dependencies
├── docs/                # Source documents (JSON files organized by category)
│   ├── CATEGORY_A/
│   ├── CATEGORY_B/
│   └── ...
├── storage/             # Persistent FAISS index (auto-generated)
└── .env.example         # Environment variables
```

## Quick Setup with Script

The easiest way to get started is using the automated setup script:

```bash
# Give execution permissions to the script (if needed)
chmod +x setup_env.sh

# Run the setup script
./setup_env.sh
```

The script will automatically:
1. Create a Python virtual environment in the `venv/` folder
2. Install all basic dependencies
3. Offer the option to install dependencies for additional providers (Ollama, HuggingFace)
4. Create a `.env` file with default configuration

## Quick Start (manual)

If you prefer to set up the environment manually:

```bash
# 1. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add OpenAI key (if using OpenAI as provider)
cp .env.example .env
echo 'OPENAI_API_KEY=sk‑...' >> .env

# 4. Prepare the knowledge base
python ingest.py          # Reads JSON files in ./docs and builds the FAISS index

# 5. Run the API
python app.py
```

## Using Different Model Providers

This project supports multiple language model (LLM) and embedding providers:

### Available Providers:
- **OpenAI**: GPT models and embeddings (requires API key)
- **Ollama**: Local models like Llama, Mistral (requires installing Ollama)
- **HuggingFace**: Local models or via API

### Configuration through Environment Variables

You can configure providers in the `.env` file:

```
OPENAI_API_KEY=sk-...        # Required for using OpenAI

# Provider configuration
LLM_PROVIDER=openai          # openai, ollama, huggingface 
LLM_MODEL=gpt-4o-mini        # Specific to each provider
EMBEDDING_PROVIDER=openai    # openai, ollama, huggingface
EMBEDDING_MODEL=text-embedding-3-large
```

### Command Line Configuration

When starting the server you can specify providers:

```bash
# Example with OpenAI
python app.py --llm-provider openai --llm-model gpt-4o-mini

# Example with Ollama (requires Ollama to be installed)
python app.py --llm-provider ollama --llm-model mistral --embedding-provider ollama --embedding-model nomic-embed-text
```

### Installing Dependencies for Different Providers

To use providers other than OpenAI, uncomment and install the necessary dependencies in `requirements.txt`:

```bash
# For HuggingFace
pip install langchain-huggingface transformers torch sentence-transformers accelerate
```

## Querying the API

The API starts at http://localhost:5000 with the following documentation:

- **GET /** - API documentation
- **GET /health** - Check service status
- **GET /config** - View current model configuration
- **GET /providers** - List available providers
- **POST /ask** - Make knowledge base queries

### Query Example:

```bash
curl -X POST http://localhost:5000/ask \
     -H 'Content-Type: application/json' \
     -d '{"message": "What is the capital of France?"}'
```

### Response:

```json
{
  "answer": "The capital of France is Paris. It is the largest city in France and serves as the country's political, economic, and cultural center.",
  "sources": [
    {
      "source": "/path/to/ragify/docs/GEOGRAPHY/france.json",
      "title": "France Information",
      "url": "https://example.com/france",
      "snippet": "Title: France Information\n\nDescription: France is a country located in Western Europe. Its capital is Paris, which is known for..."
    }
  ]
}
```

## Performance Testing

The project includes tools to test and compare different model configurations:

```bash
# Test a single configuration
python test_models.py --model-name "test_name"

# Test multiple model configurations automatically
./test_multiple_models.sh
```

## Customization

* Add more document files in `docs/`:
  * JSON files following the existing structure
  * Plain text (.txt) files
  * Markdown (.md) files 
* Run `python ingest.py` after adding new documents to rebuild the index.
* You can modify the prompt in `rag_chain.py` to adjust how queries are processed.
* To add conversational history, you can extend the system using `ConversationalRetrievalChain` from LangChain.

## Recreating the Index with Different Embeddings

If you want to change the embedding provider, you'll need to rebuild the FAISS index:

```bash
# Rebuild the index with a specific provider and model
python ingest.py --provider ollama --model nomic-embed-text
```

## Main Dependencies

- Flask: Lightweight web framework
- LangChain: Framework for LLM-based applications
- FAISS: Library for similarity search and vector clustering
- OpenAI/Ollama/HuggingFace: Language model and embedding providers