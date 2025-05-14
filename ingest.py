import os
import json
from pathlib import Path
from typing import Optional, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from model_providers import get_embeddings_model

# Try to import PyPDF2 for PDF support
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("PyPDF2 not found. PDF support disabled. Install with: pip install PyPDF2")

# Part of the ragify framework - a RAG system for knowledge-based Q&A
DOCS_DIR = Path(__file__).resolve().parent / 'docs'

def process_json_file(json_path: Path) -> List[Document]:
    """Process a JSON file and convert it to Document objects.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        List of Document objects created from the JSON file
    """
    documents = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Extract content from JSON structure
        content_parts = []
        content_parts.append(f"Title: {data.get('title', 'No title')}")
        content_parts.append(f"Description: {data.get('description', 'No description')}")
        
        # Process requirements if they exist
        if 'requirements' in data:
            for req in data['requirements']:
                if 'title' in req and 'content' in req:
                    content_parts.append(f"{req['title']}: {req['content']}")
        
        # Create document with content and metadata
        content = "\n\n".join(content_parts)
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": str(json_path),
                    "title": data.get("title", ""),
                    "url": data.get("url", ""),
                    "file_type": "json"
                }
            )
        )
        
    except Exception as e:
        print(f"Error processing JSON file {json_path}: {e}")
    
    return documents

def process_text_file(text_path: Path) -> List[Document]:
    """Process a text file and convert it to Document objects.
    
    Args:
        text_path: Path to the text file
        
    Returns:
        List of Document objects created from the text file
    """
    documents = []
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract a title from the filename
        filename = text_path.name
        title = filename.replace('.txt', '').replace('.md', '').replace('_', ' ').replace('-', ' ').title()
        
        # Create document with content and metadata
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": str(text_path),
                    "title": title,
                    "file_type": "text"
                }
            )
        )
        
    except Exception as e:
        print(f"Error processing text file {text_path}: {e}")
    
    return documents

def process_pdf_file(pdf_path: Path) -> List[Document]:
    """Process a PDF file and convert it to Document objects.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of Document objects created from the PDF file
    """
    documents = []
    
    if not PDF_SUPPORT:
        print(f"Skipping PDF file {pdf_path}: PyPDF2 not installed")
        return documents
    
    try:
        # Extract a title from the filename
        filename = pdf_path.name
        title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
        
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages in the PDF
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            full_text = ""
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                full_text += page.extract_text() + "\n\n"
            
            # Create document with content and metadata
            documents.append(
                Document(
                    page_content=full_text,
                    metadata={
                        "source": str(pdf_path),
                        "title": title,
                        "file_type": "pdf",
                        "pages": num_pages
                    }
                )
            )
        
    except Exception as e:
        print(f"Error processing PDF file {pdf_path}: {e}")
    
    return documents

def ingest_and_build(output_path: str, embedding_provider: str = "openai", embedding_model: Optional[str] = None):
    """Load JSON, text, and PDF files under docs/ and build a persistent FAISS vector store.

    Args:
        output_path: Where to store the FAISS index directory
        embedding_provider: Provider for embeddings ("openai", "ollama", "huggingface")
        embedding_model: Optional specific model to use for embeddings

    Returns:
        Initialized FAISS vector store
    """
    documents = []
    
    # Recursively process all JSON files in subdirectories
    json_count = 0
    for json_path in DOCS_DIR.glob('**/*.json'):
        docs = process_json_file(json_path)
        documents.extend(docs)
        json_count += 1
    
    # Recursively process all text files (txt and md) in subdirectories
    text_count = 0
    for text_extension in ["*.txt", "*.md"]:
        for text_path in DOCS_DIR.glob(f'**/{text_extension}'):
            docs = process_text_file(text_path)
            documents.extend(docs)
            text_count += 1
    
    # Recursively process all PDF files in subdirectories
    pdf_count = 0
    if PDF_SUPPORT:
        for pdf_path in DOCS_DIR.glob('**/*.pdf'):
            docs = process_pdf_file(pdf_path)
            documents.extend(docs)
            pdf_count += 1
    
    # Split the documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(documents)
    
    print(f"Processed {json_count} JSON files, {text_count} text files, and {pdf_count} PDF files into {len(splits)} chunks")

    # Create vector store with the specified embedding model
    embeddings = get_embeddings_model(provider=embedding_provider, model_name=embedding_model)
    print(f"Using embeddings model from provider: {embedding_provider}")
    
    vector_store = FAISS.from_documents(splits, embeddings)
    vector_store.save_local(output_path)
    print(f"Vector store saved to {output_path}")
    return vector_store

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest documents and build vector store')
    parser.add_argument('--output', type=str, default='storage', 
                      help='Output directory for the FAISS index')
    parser.add_argument('--provider', type=str, default='openai',
                      help='Embedding provider (openai, ollama, huggingface)')
    parser.add_argument('--model', type=str, default=None,
                      help='Specific embedding model to use')
    
    args = parser.parse_args()
    
    output_path = str(Path(__file__).resolve().parent / args.output)
    ingest_and_build(output_path, args.provider, args.model)