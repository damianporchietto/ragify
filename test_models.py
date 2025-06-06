#!/usr/bin/env python3
"""
Script to test different model configurations in the Ragify framework.
Sends a set of test questions to the server and saves the responses.
"""

import os
import requests
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Import config manager
from config_manager import config

def test_model(model_name, questions, api_url=None, timeout=None):
    """
    Test a model with a set of questions.
    
    Args:
        model_name: Name of the model to test (for naming result files)
        questions: List of questions to send
        api_url: Base API URL
        timeout: Maximum wait time for each request (seconds)
    """
    # Use config defaults if not specified
    api_url = api_url or config.get_default_api_url()
    timeout = timeout or config.get_default_timeout()
    
    print(f"Testing model: {model_name}")
    print(f"API URL: {api_url}")
    print(f"Questions: {len(questions)}")
    
    # Check if the server is active
    try:
        health_check = requests.get(f"{api_url}/health", timeout=config.get_health_check_timeout())
        if health_check.status_code != 200:
            print(f"Error: Server not responding correctly. Status: {health_check.status_code}")
            return False
    except Exception as e:
        print(f"Error: Cannot connect to server at {api_url}. {str(e)}")
        return False
    
    # Get the current server configuration
    try:
        config_resp = requests.get(f"{api_url}/config", timeout=config.get_health_check_timeout())
        if config_resp.status_code == 200:
            server_config = config_resp.json()
            print(f"Server Configuration:")
            print(f"  LLM: {server_config['llm']['provider']} {server_config['llm']['model'] or '(default)'}")
            print(f"  Embeddings: {server_config['embeddings']['provider']} {server_config['embeddings']['model'] or '(default)'}")
        else:
            print("Warning: Could not get server configuration")
    except Exception:
        print("Warning: Could not get server configuration")
    
    # Create folder for results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(f"{config.get_results_dir_prefix()}_{model_name}_{timestamp}")
    results_dir.mkdir(exist_ok=True)
    
    results = {
        "model": model_name,
        "timestamp": timestamp,
        "api_url": api_url,
        "results": []
    }
    
    # Test each question
    for i, question in enumerate(questions):
        print(f"Testing question {i+1}/{len(questions)}: {question[:50]}...")
        
        try:
            response = requests.post(
                f"{api_url}/ask",
                json={"message": question},
                timeout=timeout
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

def main():
    parser = argparse.ArgumentParser(description='Test RAG models with different configurations')
    parser.add_argument('--model-name', type=str, default="current_model",
                      help='Name to identify this test run')
    parser.add_argument('--questions-file', type=str, default=None,
                      help='File containing questions (one per line)')
    parser.add_argument('--api-url', type=str, default=config.get_default_api_url(),
                      help='Base URL of the API')
    parser.add_argument('--timeout', type=int, default=config.get_default_timeout(),
                      help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Load questions from file or use default
    if args.questions_file:
        try:
            with open(args.questions_file, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f if line.strip()]
                if not questions:
                    print("Warning: No questions found in file. Using default questions.")
                    questions = config.get_default_questions()
        except Exception as e:
            print(f"Error loading questions from file: {str(e)}")
            print("Using default questions instead.")
            questions = config.get_default_questions()
    else:
        questions = config.get_default_questions()
    
    # Run the tests
    test_model(args.model_name, questions, args.api_url, args.timeout)

if __name__ == "__main__":
    main() 