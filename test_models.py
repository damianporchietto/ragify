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

# Predefined test questions
DEFAULT_QUESTIONS = [
    "What is the capital of France?",
    "How do I make sourdough bread?",
    "What equipment do I need for a podcast?",
    "What are the best practices for data security?",
    "What are the steps to create a website?"
]

def test_model(model_name, questions, api_url="http://localhost:5000", timeout=60):
    """
    Test a model with a set of questions.
    
    Args:
        model_name: Name of the model to test (for naming result files)
        questions: List of questions to send
        api_url: Base API URL
        timeout: Maximum wait time for each request (seconds)
    """
    print(f"Testing model: {model_name}")
    print(f"API URL: {api_url}")
    print(f"Questions: {len(questions)}")
    
    # Check if the server is active
    try:
        health_check = requests.get(f"{api_url}/health", timeout=5)
        if health_check.status_code != 200:
            print(f"Error: Server not responding correctly. Status: {health_check.status_code}")
            return False
    except Exception as e:
        print(f"Error: Cannot connect to server at {api_url}. {str(e)}")
        return False
    
    # Get the current server configuration
    try:
        config_resp = requests.get(f"{api_url}/config", timeout=5)
        if config_resp.status_code == 200:
            config = config_resp.json()
            print(f"Server Configuration:")
            print(f"  LLM: {config['llm']['provider']} {config['llm']['model'] or '(default)'}")
            print(f"  Embeddings: {config['embeddings']['provider']} {config['embeddings']['model'] or '(default)'}")
        else:
            print("Warning: Could not get server configuration")
    except Exception:
        print("Warning: Could not get server configuration")
    
    # Create folder for results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(f"results_{model_name}_{timestamp}")
    results_dir.mkdir(exist_ok=True)
    
    results = {
        "model": model_name,
        "timestamp": timestamp,
        "api_url": api_url,
        "results": []
    }
    
    # Test each question
    for i, question in enumerate(questions):
        print(f"\nTesting question {i+1}/{len(questions)}:")
        print(f"  Q: {question}")
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{api_url}/ask",
                json={"message": question},
                timeout=timeout
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Print a summary of the response
                answer = result.get("answer", "")
                print(f"  A: {answer[:100]}..." if len(answer) > 100 else f"  A: {answer}")
                print(f"  Time: {elapsed_time:.2f} seconds")
                
                # Save the result in the results dictionary
                results['results'].append({
                    "question": question,
                    "answer": answer,
                    "sources": result.get("sources", []),
                    "response_time": elapsed_time
                })
                
                print(f"  ✓ Success")
            else:
                print(f"  ✗ Error: {response.status_code} - {response.text}")
                results['results'].append({
                    "question": question,
                    "error": f"Status {response.status_code}: {response.text}",
                    "response_time": elapsed_time
                })
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"  ✗ Exception: {str(e)}")
            results['results'].append({
                "question": question,
                "error": str(e),
                "response_time": elapsed_time
            })
        
        # Wait to avoid overloading the API
        time.sleep(1)
    
    # Save all results in a single JSON file
    results_file = results_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Calculate basic statistics
    successful_queries = sum(1 for r in results['results'] if 'error' not in r)
    avg_time = sum(r.get('response_time', 0) for r in results['results']) / len(results['results'])
    
    print("\nTesting complete!")
    print(f"Results saved to: {results_file}")
    print(f"Success rate: {successful_queries}/{len(questions)} ({successful_queries/len(questions)*100:.1f}%)")
    print(f"Average response time: {avg_time:.2f} seconds")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Test RAG models with different configurations')
    parser.add_argument('--model-name', type=str, default="current_model",
                      help='Name to identify this test run')
    parser.add_argument('--questions-file', type=str, default=None,
                      help='File containing questions (one per line)')
    parser.add_argument('--api-url', type=str, default="http://localhost:5000",
                      help='Base URL of the API')
    parser.add_argument('--timeout', type=int, default=60,
                      help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Load questions from file or use default
    if args.questions_file:
        try:
            with open(args.questions_file, 'r', encoding='utf-8') as f:
                questions = [line.strip() for line in f if line.strip()]
                if not questions:
                    print("Warning: No questions found in file. Using default questions.")
                    questions = DEFAULT_QUESTIONS
        except Exception as e:
            print(f"Error loading questions from file: {str(e)}")
            print("Using default questions instead.")
            questions = DEFAULT_QUESTIONS
    else:
        questions = DEFAULT_QUESTIONS
    
    # Run the tests
    test_model(args.model_name, questions, args.api_url, args.timeout)

if __name__ == "__main__":
    main() 