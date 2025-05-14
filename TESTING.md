# Ragify Testing Guide

This document provides instructions for testing and using the RAG system implemented for knowledge-based question answering.

## Automated Setup (Recommended)

To quickly and easily set up the environment, use the included configuration script:

```bash
# Give execution permissions (if needed)
chmod +x setup_env.sh

# Run configuration script
./setup_env.sh
```

This script:
1. Creates a Python virtual environment
2. Installs all necessary dependencies
3. Lets you choose which model providers you want to use
4. Sets up a `.env` file with default values

## Manual Setup

If you prefer to set up the environment manually:

1. Make sure you've installed all dependencies:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your OpenAI API key:
   ```bash
   echo 'OPENAI_API_KEY=sk-your-api-key-here' > .env
   ```

3. Build the vector database:
   ```bash
   python ingest.py
   ```
   This will process all JSON files in the `docs/` directory and create a FAISS index in the `storage/` folder.

## Starting the Server

Run the Flask application:
```bash
python app.py
```

By default, the server will start at `http://localhost:5000`.

## Basic Tests

### 1. Check the service status

```bash
curl http://localhost:5000/health
```

You should receive a response like:
```json
{"status": "ok"}
```

### 2. View the documentation

Open in your browser: `http://localhost:5000/`

You should see the HTML documentation page describing the available endpoints.

### 3. Make knowledge base queries

You can test the system with different queries related to your knowledge base:

#### Example 1: Basic query

```bash
curl -X POST http://localhost:5000/ask \
     -H 'Content-Type: application/json' \
     -d '{"message": "What is the capital of France?"}'
```

#### Example 2: Specific requirements

```bash
curl -X POST http://localhost:5000/ask \
     -H 'Content-Type: application/json' \
     -d '{"message": "What are the steps to make a sourdough bread?"}'
```

#### Example 3: Cost query

```bash
curl -X POST http://localhost:5000/ask \
     -H 'Content-Type: application/json' \
     -d '{"message": "What equipment do I need for starting a podcast?"}'
```

## Testing with Different Model Providers

The system now allows testing different language model (LLM) and embedding providers.

### 1. Check available providers

```bash
curl http://localhost:5000/providers
```

You should receive information about the available providers.

### 2. Check current configuration

```bash
curl http://localhost:5000/config
```

### 3. Testing with OpenAI (default configuration)

```bash
# Start the server with OpenAI (default)
python app.py

# Make queries normally
curl -X POST http://localhost:5000/ask \
     -H 'Content-Type: application/json' \
     -d '{"message": "What is the capital of France?"}'
```

### 4. Testing with Ollama (local models)

First, make sure you have Ollama installed and running:
```bash
# Install Ollama according to instructions at https://ollama.ai/

# Download necessary models
ollama pull mistral
ollama pull nomic-embed-text

# Install necessary dependencies
pip install langchain_community
```

Then, run the server with Ollama as the provider:
```bash
python app.py --llm-provider ollama --llm-model mistral --embedding-provider ollama --embedding-model nomic-embed-text
```

If you need to recreate the index with Ollama embeddings:
```bash
python ingest.py --provider ollama --model nomic-embed-text
```

### 5. Testing with HuggingFace (local models or API)

First, install the necessary dependencies:
```bash
pip install langchain-huggingface transformers torch sentence-transformers accelerate
```

Then, run the server with HuggingFace as the provider:
```bash
python app.py --llm-provider huggingface --llm-model google/flan-t5-base --embedding-provider huggingface --embedding-model BAAI/bge-small-en-v1.5
```

If you need to recreate the index with HuggingFace embeddings:
```bash
python ingest.py --provider huggingface --model BAAI/bge-small-en-v1.5
```

## Comparing Results Between Different Models

To evaluate and compare the performance of different models, you can:

1. Prepare a set of test questions in a file (e.g., `test_questions.txt`).
2. Create a script that sends each question to the server and saves the responses.
3. Run the script with different model configurations.
4. Compare the answers for each question.

Example test script (save as `test_models.py`):

```python
import requests
import json
import time
from pathlib import Path

# Load test questions
with open('test_questions.txt', 'r') as f:
    questions = [line.strip() for line in f if line.strip()]

# Configure model to test
model_name = "openai"  # Change according to the model being tested

# Folder for results
results_dir = Path(f"results_{model_name}")
results_dir.mkdir(exist_ok=True)

# Test each question
for i, question in enumerate(questions):
    print(f"Testing question {i+1}/{len(questions)}: {question[:50]}...")
    
    try:
        response = requests.post(
            "http://localhost:5000/ask",
            json={"message": question},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Save result
            with open(results_dir / f"q{i+1}.json", 'w') as f:
                json.dump({
                    "question": question,
                    "answer": result.get("answer"),
                    "sources": result.get("sources", [])
                }, f, indent=2)
                
            print(f"  ✓ Success")
        else:
            print(f"  ✗ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"  ✗ Exception: {str(e)}")
    
    # Wait to avoid overloading the API
    time.sleep(1)

print("Testing complete!")
```

## Automating Tests for Multiple Models

To facilitate testing with different configurations, you can use the `test_multiple_models.sh` script:

```bash
# Run automated tests with different model configurations
./test_multiple_models.sh
```

This script:
1. Creates a test questions file if it doesn't exist
2. Checks dependencies and model availability
3. Automatically tests different model configurations

## Evaluation of the System

To evaluate the quality of the answers, consider the following aspects:

1. **Precision**: Does the answer contain correct information based on the source documents?
2. **Relevance**: Does the answer directly address the user's query?
3. **Sources**: Are the sources cited correctly?
4. **Completeness**: Does the answer provide all necessary information?
5. **Clarity**: Is the answer easy to understand?
6. **Speed**: How long does each model take to respond?
7. **Robustness**: Does the model handle ambiguous or poorly formulated queries well?

## Possible Improvements

If you want to expand the system, consider:

1. Adding more documents to the knowledge base:
   - JSON files (structured data)
   - Text files (.txt)
   - Markdown files (.md)
   - Support for additional file formats like PDF or DOC
2. Implementing a conversation history to maintain context between queries.
3. Improving the prompt in `rag_chain.py` to get more specific answers.
4. Adding document filtering by relevance or category.
5. Implementing a web frontend for easier queries.
6. Adding support for more model providers.
7. Implementing cache mechanisms to improve performance.

## Troubleshooting

### Error Loading Embedding Model

If you receive an error related to the OpenAI API, check that:
- Your API key in the `.env` file is valid
- You have sufficient balance in your OpenAI account
- Your internet connection works correctly

### Error with Ollama

If you have problems using Ollama:
- Verify that Ollama is installed and running
- Check that you've downloaded the necessary models
- Ensure that `langchain_community` is installed

### Error with HuggingFace

If you have problems using HuggingFace models:
- Verify that all dependencies are installed
- Ensure you have enough RAM and disk space
- Consider using smaller models if you have resource limitations

### Error Processing JSON Documents

If you encounter problems processing JSON documents:
- Verify that all JSON files have the correct format
- Ensure that the path to the `docs/` directory is accessible
- Check that you have write permissions to create the `storage/` folder

### Server Not Starting

If the Flask server doesn't start:
- Verify that port 5000 isn't in use
- Ensure that all dependencies are installed correctly
- Check the error logs for specific problems 