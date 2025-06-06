#!/bin/bash
# Script to test multiple model configurations

set -e  # Exit on error

# Read port from config file if available, otherwise use default
if command -v python3 &> /dev/null && [ -f "config.yaml" ]; then
    PORT=$(python3 -c "
import yaml
try:
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print(config.get('server', {}).get('port', 5000))
except:
    print(5000)
" 2>/dev/null || echo 5000)
else
    PORT=5000
fi

API_URL="http://localhost:$PORT"
QUESTIONS_FILE="test_questions.txt"

# If the questions file doesn't exist, create it with default questions
if [ ! -f "$QUESTIONS_FILE" ]; then
  echo "Creating sample questions file..."
  cat > "$QUESTIONS_FILE" << EOF
What is the capital of France?
How do I make sourdough bread?
What equipment do I need for a podcast?
What are the best practices for data security?
What are the steps to create a website?
EOF
  echo "File $QUESTIONS_FILE created."
fi

# Function to run tests
run_test() {
  local model_name=$1
  local llm_provider=$2
  local llm_model=$3
  local embedding_provider=$4
  local embedding_model=$5
  
  echo ""
  echo "====================================="
  echo "TESTING CONFIGURATION: $model_name"
  echo "====================================="
  echo "LLM Provider: $llm_provider"
  echo "LLM Model: ${llm_model:-default}"
  echo "Embedding Provider: $embedding_provider"
  echo "Embedding Model: ${embedding_model:-default}"
  echo "====================================="
  
  # Start the server with the specific configuration
  echo "Starting server..."
  python app.py --llm-provider "$llm_provider" \
                --llm-model "$llm_model" \
                --embedding-provider "$embedding_provider" \
                --embedding-model "$embedding_model" \
                --port "$PORT" &
  
  SERVER_PID=$!
  
  # Wait for the server to be ready
  echo "Waiting for the server to be ready..."
  sleep 5
  
  # Run tests
  echo "Running tests..."
  python test_models.py --model-name "$model_name" --questions-file "$QUESTIONS_FILE" --api-url "$API_URL"
  
  # Stop the server
  echo "Stopping server (PID: $SERVER_PID)..."
  kill $SERVER_PID
  wait $SERVER_PID 2>/dev/null || true
  sleep 2
}

# Make sure the virtual environment and dependencies are installed
check_dependencies() {
  case "$1" in
    "openai")
      if [ -z "$OPENAI_API_KEY" ]; then
        echo "WARNING: OPENAI_API_KEY is not set in the environment"
      fi
      ;;
    "ollama")
      if ! command -v ollama &> /dev/null; then
        echo "WARNING: Ollama does not appear to be installed"
      else
        echo "Checking Ollama models..."
        if ! ollama list | grep -q "$2"; then
          echo "Model '$2' is not available in Ollama. You can download it with: ollama pull $2"
        fi
      fi
      ;;
    "huggingface")
      echo "Checking dependencies for HuggingFace..."
      if ! pip list | grep -q "transformers"; then
        echo "WARNING: The 'transformers' package is not installed"
        echo "To install: pip install transformers torch sentence-transformers"
      fi
      ;;
  esac
}

# Configurations to test
echo "Preparing multiple model tests..."

# OpenAI tests (if there's an API key)
if [ -n "$OPENAI_API_KEY" ]; then
  check_dependencies "openai"
  run_test "openai_gpt4o_mini" "openai" "gpt-4o-mini" "openai" "text-embedding-3-large"
else
  echo "Skipping OpenAI tests (OPENAI_API_KEY not found)"
fi

# Ollama tests (if installed)
if command -v ollama &> /dev/null; then
  check_dependencies "ollama" "mistral"
  run_test "ollama_mistral" "ollama" "mistral" "ollama" "nomic-embed-text"
else
  echo "Skipping Ollama tests (not installed)"
fi

# HuggingFace tests (if dependencies are installed)
if pip list | grep -q "transformers"; then
  check_dependencies "huggingface"
  run_test "huggingface_flan_t5" "huggingface" "google/flan-t5-base" "huggingface" "BAAI/bge-small-en-v1.5"
else
  echo "Skipping HuggingFace tests (dependencies not installed)"
fi

echo ""
echo "=========================================="
echo "ALL TESTS COMPLETED"
echo "Check the 'results_*' folders to see the results of each test."
echo "==========================================" 