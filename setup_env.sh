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


# Read default port from config file if available
DEFAULT_PORT=5000
if [ -f "${PROJECT_DIR}/config.yaml" ]; then
    DEFAULT_PORT=$(python3 -c "
import yaml
try:
    with open('${PROJECT_DIR}/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print(config.get('server', {}).get('port', 5000))
except:
    print(5000)
" 2>/dev/null || echo 5000)
fi

# Generate a starter .env file if it doesn't exist
ENV_FILE="${PROJECT_DIR}/.env"
if [ ! -f "${ENV_FILE}" ]; then
    echo -e "\n${GREEN}Creating .env file with default settings...${NC}"
    cat > "${ENV_FILE}" << EOF
# OpenAI API Key - required for OpenAI models
# OPENAI_API_KEY=sk-your-api-key-here

# Port for the Flask application
PORT=${DEFAULT_PORT}

# Default model providers

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