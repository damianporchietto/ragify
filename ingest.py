import os
import json
from pathlib import Path
from typing import Optional, List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from model_providers import get_embeddings_model
from config_manager import config

# Explicitly reload config to ensure latest values are used
config.load_config()

# Try to import PyPDF2 for PDF support
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("PyPDF2 not found. PDF support disabled. Install with: pip install PyPDF2")

# Part of the ragify framework - a RAG system for knowledge-based Q&A
DOCS_DIR = Path(__file__).resolve().parent / config.get_docs_dir()

def flatten_json_to_text(data, parent_key='', separator=': ', max_depth=10, current_depth=0):
    """
    Recursively flatten any JSON structure into human-readable text.
    
    Args:
        data: The JSON data (dict, list, or primitive)
        parent_key: The parent key for nested structures
        separator: Separator between key and value
        max_depth: Maximum recursion depth to prevent infinite loops
        current_depth: Current recursion depth
        
    Returns:
        List of formatted text lines
    """
    if current_depth > max_depth:
        return [f"{parent_key}: [Max depth reached]"]
    
    lines = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            # Format the key nicely
            formatted_key = key.replace('_', ' ').replace('-', ' ').title()
            full_key = f"{parent_key}.{formatted_key}" if parent_key else formatted_key
            
            if isinstance(value, (dict, list)):
                # Add section header for complex structures
                if value:  # Only add if not empty
                    lines.append(f"\n{full_key}:")
                    lines.extend(flatten_json_to_text(value, full_key, separator, max_depth, current_depth + 1))
            elif value is not None and str(value).strip():  # Skip empty/null values
                lines.append(f"{full_key}{separator}{value}")
                
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                item_key = f"{parent_key}[{i+1}]" if parent_key else f"Item {i+1}"
                lines.extend(flatten_json_to_text(item, item_key, separator, max_depth, current_depth + 1))
            elif item is not None and str(item).strip():
                lines.append(f"{parent_key}[{i+1}]{separator}{item}")
                
    else:
        # Primitive value
        if data is not None and str(data).strip():
            lines.append(f"{parent_key}{separator}{data}")
    
    return lines

def process_json_file(json_path: Path) -> List[Document]:
    """Process a JSON file and convert it to Document objects.
    
    This function can handle any JSON structure by recursively flattening it
    into human-readable text format.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        List of Document objects created from the JSON file
    """
    documents = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Use generic flattening to convert any JSON structure to text
        content_lines = flatten_json_to_text(data)
        content = "\n".join(content_lines)
        
        # Extract metadata - try common fields but don't fail if they don't exist
        title = ""
        url = ""
        if isinstance(data, dict):
            # Try common title fields
            for title_field in ['title', 'name', 'subject', 'heading', 'label']:
                if title_field in data and data[title_field]:
                    title = str(data[title_field])
                    break
            
            # Try common URL fields
            for url_field in ['url', 'link', 'href', 'uri', 'web_url', 'website']:
                if url_field in data and data[url_field]:
                    url = str(data[url_field])
                    break
        
        # Debug logging to monitor content extraction
        print(f"Processing JSON: {json_path.name}")
        print(f"Extracted content length: {len(content)} characters")
        print(f"Content preview: {content[:200]}...")
        
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": str(json_path),
                    "title": title,
                    "url": url,
                    "file_type": "json",
                    "content_length": len(content),
                    "filename": json_path.name
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

def ingest_and_build(collection_name: str = None, embedding_provider: str = None, embedding_model: Optional[str] = None, force_rebuild: bool = False):
    """Load JSON, text, and PDF files under docs/ and build a persistent Qdrant vector store.

    Args:
        collection_name: Name of the Qdrant collection (uses config default if None)
        embedding_provider: Provider for embeddings ("openai", "vertexai")
        embedding_model: Optional specific model to use for embeddings
        force_rebuild: Whether to recreate the collection even if it exists

    Returns:
        Initialized Qdrant vector store
    """
    # Use config defaults if not specified
    embedding_provider = embedding_provider or config.get_default_embedding_provider()
    collection_name = collection_name or config.get('vector_store', {}).get('qdrant_collection_name', 'my_collection')
    
    # Get Qdrant configuration
    qdrant_url = config.get('vector_store', {}).get('qdrant_url', 'http://localhost:6333')
    distance_metric = config.get('vector_store', {}).get('qdrant_distance_metric', 'Cosine')
    
    # Create embeddings model to get dimension
    embeddings = get_embeddings_model(provider=embedding_provider, model_name=embedding_model)
    print(f"Using embeddings model from provider: {embedding_provider}")
    
    # Initialize Qdrant client
    client = QdrantClient(url=qdrant_url)
    
    # Check if collection exists and handle accordingly
    try:
        collection_info = client.get_collection(collection_name)
        if force_rebuild:
            print(f"Force rebuild requested. Recreating collection '{collection_name}'...")
            client.delete_collection(collection_name)
            collection_exists = False
        else:
            print(f"Collection '{collection_name}' already exists with {collection_info.points_count} points")
            collection_exists = True
    except Exception:
        collection_exists = False
    
    # Only process documents if collection doesn't exist or force rebuild
    if not collection_exists:
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
        
        # Split the documents using configurable parameters
        chunk_size = config.get_chunk_size()
        chunk_overlap = config.get_chunk_overlap()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        splits = splitter.split_documents(documents)
        
        print(f"Processed {json_count} JSON files, {text_count} text files, and {pdf_count} PDF files")
        print(f"Document chunking: {len(documents)} documents -> {len(splits)} chunks")
        print(f"Chunk settings: size={chunk_size}, overlap={chunk_overlap}")
        
        # Debug: Show sample chunk information
        if splits:
            print(f"Sample chunk preview (first chunk):")
            print(f"  Length: {len(splits[0].page_content)} characters")
            print(f"  Content: {splits[0].page_content[:150]}...")
            print(f"  Metadata: {splits[0].metadata}")
        
        # Get embedding dimension by creating a test embedding
        test_embedding = embeddings.embed_query("test")
        embedding_dim = len(test_embedding)
        
        # Map distance metric string to Qdrant Distance enum
        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclidean": Distance.EUCLID,
            "Dot": Distance.DOT
        }
        qdrant_distance = distance_map.get(distance_metric, Distance.COSINE)
        
        # Create collection with proper vector configuration
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name)
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dim, distance=qdrant_distance),
        )
        print(f"Created Qdrant collection '{collection_name}' with {embedding_dim}D vectors using {distance_metric} distance")
        
        # Create Qdrant vector store and add documents
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embeddings
        )
        
        # Add documents to the vector store
        if splits:
            vector_store.add_documents(splits)
            print(f"Added {len(splits)} document chunks to Qdrant collection '{collection_name}'")
    else:
        # Collection exists, just create the vector store interface
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embeddings
        )
        print(f"Using existing Qdrant collection '{collection_name}'")

    return vector_store

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest documents and build Qdrant vector store')
    parser.add_argument('--provider', type=str, default=config.get_default_embedding_provider(),
                        help='Embedding provider (openai, vertexai)')
    parser.add_argument('--model', type=str, default=config.get_default_embedding_model(),
                        help='Specific embedding model to use')
    parser.add_argument('--collection', type=str,
                        default=config.get('vector_store', {}).get('qdrant_collection_name', 'my_collection'),
                        help='Qdrant collection name')
    parser.add_argument('--force-rebuild', action='store_true',
                        help='Force rebuild of the collection even if it exists')
    
    args = parser.parse_args()
    
    ingest_and_build(args.collection, args.provider, args.model, args.force_rebuild)