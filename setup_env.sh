#!/bin/bash
# Script to set up a Python virtual environment and install all requirements

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project directory is where this script is located
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
REQUIREMENTS_FILE="${PROJECT_DIR}/requirements.txt"

echo -e "${GREEN}=== RAG Flask Project Setup ===${NC}"
echo "Project directory: ${PROJECT_DIR}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Detected Python version: ${PYTHON_VERSION}"

# Check if python3-venv is installed on Debian/Ubuntu
if [[ -f /etc/debian_version ]] && ! dpkg -l python3-venv &> /dev/null; then
    echo -e "${YELLOW}Warning: python3-venv package may not be installed.${NC}"
    echo "You may need to install it with: sudo apt install python3-venv"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "${VENV_DIR}" ]; then
    echo -e "\n${GREEN}Creating virtual environment in ${VENV_DIR}...${NC}"
    python3 -m venv "${VENV_DIR}"
    echo "Virtual environment created."
else
    echo -e "\n${YELLOW}Virtual environment already exists at ${VENV_DIR}${NC}"
    echo "Will use the existing environment."
fi

# Activate the virtual environment
echo -e "\n${GREEN}Activating virtual environment...${NC}"
source "${VENV_DIR}/bin/activate"

# Upgrade pip, setuptools, and wheel
echo -e "\n${GREEN}Upgrading pip, setuptools, and wheel...${NC}"
pip install --upgrade pip setuptools wheel

# Install basic requirements
echo -e "\n${GREEN}Installing base requirements from ${REQUIREMENTS_FILE}...${NC}"
pip install -r "${REQUIREMENTS_FILE}"

# Ask if user wants to install optional dependencies
echo -e "\n${YELLOW}Do you want to install optional dependencies for additional model providers?${NC}"
echo "1) OpenAI only (already installed with base requirements)"
echo "2) Add Ollama support (local models)"
echo "3) Add HuggingFace support (requires more disk space)"
echo "4) Install all dependencies (recommended for full testing)"
echo "Enter your choice (1-4):"
read -r choice

case $choice in
    2)
        echo -e "\n${GREEN}Installing Ollama dependencies...${NC}"
        pip install langchain_community
        ;;
    3)
        echo -e "\n${GREEN}Installing HuggingFace dependencies...${NC}"
        pip install langchain-huggingface transformers torch sentence-transformers accelerate
        ;;
    4)
        echo -e "\n${GREEN}Installing all optional dependencies...${NC}"
        pip install langchain_community langchain-huggingface transformers torch sentence-transformers accelerate
        ;;
    *)
        echo -e "\n${GREEN}Skipping optional dependencies.${NC}"
        ;;
esac

# Generate a starter .env file if it doesn't exist
ENV_FILE="${PROJECT_DIR}/.env"
if [ ! -f "${ENV_FILE}" ]; then
    echo -e "\n${GREEN}Creating .env file with default settings...${NC}"
    cat > "${ENV_FILE}" << EOF
# OpenAI API Key - required for OpenAI models
# OPENAI_API_KEY=sk-your-api-key-here

# Port for the Flask application
PORT=5000

# Default model providers
LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o-mini

EMBEDDING_PROVIDER=openai
# EMBEDDING_MODEL=text-embedding-3-large

# Debug mode (set to empty or False in production)
FLASK_DEBUG=True
EOF
    echo "Created .env file. Edit it to add your API keys and preferences."
else
    echo -e "\n${YELLOW}A .env file already exists. Not overwriting.${NC}"
fi

# Provide instructions for next steps
echo -e "\n${GREEN}==== Setup Complete ====${NC}"
echo "To activate the virtual environment in the future, run:"
echo "    source ${VENV_DIR}/bin/activate"
echo ""
echo "To deactivate the virtual environment, simply run:"
echo "    deactivate"
echo ""
echo "To use the RAG system, run:"
echo "    1. python ingest.py (to build the vector database)"
echo "    2. python app.py (to start the Flask server)"
echo ""
echo "To run tests with different model configurations:"
echo "    ./test_multiple_models.sh"
echo ""
if [[ $choice == 1 ]]; then
    echo -e "${YELLOW}Remember to add your OpenAI API key to the .env file!${NC}"
fi

# Keep the virtual environment activated
echo -e "${GREEN}Virtual environment is now active and ready to use.${NC}" 