import os
from pathlib import Path
from typing import Dict, Any, Optional

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from model_providers import get_llm_model, get_embeddings_model
from ingest import ingest_and_build
from config_manager import config

# Explicitly reload config to ensure latest values are used
config.load_config()

class RAGPipeline:
    def __init__(self, 
                 llm_provider: str = None, 
                 llm_model: Optional[str] = None,
                 embedding_provider: str = None, 
                 embedding_model: Optional[str] = None,
                 temperature: float = None):
        """
        Initialize the RAG pipeline with configurable model providers.
        
        Args:
            llm_provider: Provider for the LLM ("openai", "vertexai")
            llm_model: Optional specific LLM model to use
            embedding_provider: Provider for embeddings ("openai", "vertexai")
            embedding_model: Optional specific embedding model to use
            temperature: Temperature for text generation
        """
        # Use config defaults if not specified
        llm_provider = llm_provider or config.get_default_llm_provider()
        embedding_provider = embedding_provider or config.get_default_embedding_provider()
        temperature = temperature if temperature is not None else config.get_temperature()
        
        # Initialize embeddings model
        self.embeddings = get_embeddings_model(provider=embedding_provider, model_name=embedding_model)
        
        # Get Qdrant configuration
        qdrant_url = config.get('vector_store', {}).get('qdrant_url', 'http://localhost:6333')
        collection_name = config.get('vector_store', {}).get('qdrant_collection_name', 'my_collection')
        
        # Initialize Qdrant client
        client = QdrantClient(url=qdrant_url)
        
        # Try to connect to existing collection, else build it
        try:
            collection_info = client.get_collection(collection_name)
            print(f"Connected to existing Qdrant collection '{collection_name}' with {collection_info.points_count} points")
            self.vector_store = QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=self.embeddings
            )
        except Exception:
            print(f"Collection '{collection_name}' not found. Building new collection...")
            # Build and persist the vectorstore
            self.vector_store = ingest_and_build(
                collection_name=collection_name,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model
            )

        # Create retriever with configurable parameters
        self.retriever = self.vector_store.as_retriever(
            search_type=config.get_search_type(),
            search_kwargs={"k": config.get_top_k_results()}
        )
        
        # Initialize LLM
        self.llm = get_llm_model(provider=llm_provider, model_name=llm_model, temperature=temperature)
        
        # Create prompt from config template
        prompt_template = config.get_rag_prompt_template()
        self.prompt = PromptTemplate.from_template(prompt_template)
        
        # Set up RAG chain using LCEL (LangChain Expression Language)
        # This is more stable than the create_retrieval_chain approach
        self.chain = (
            {"query": RunnablePassthrough(), "context": self.retriever}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def __call__(self, question: str) -> Dict[str, Any]:
        try:
            # Run the RAG chain
            answer = self.chain.invoke(question)
            
            # Get the documents from the retriever directly
            retrieved_docs = self.retriever.get_relevant_documents(question)
            
            # Format the output for consistency with app.py
            return {
                "result": answer,
                "source_documents": retrieved_docs
            }
        except Exception as e:
            # Fallback to a simpler approach if the chain fails
            print(f"Error in RAG chain: {str(e)}. Using fallback approach.")
            
            # Simple fallback using RetrievalQA
            simple_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=self.retriever,
                chain_type="stuff",
                chain_type_kwargs={"prompt": self.prompt},
                return_source_documents=True
            )
            
            result = simple_chain({"query": question})
            return {
                "result": result.get("result", ""),
                "source_documents": result.get("source_documents", [])
            }

import threading
from typing import Dict, Tuple

# Thread-safe pipeline cache
_pipeline_cache: Dict[Tuple[str, str, str, str], RAGPipeline] = {}
_cache_lock = threading.Lock()

def load_rag_chain(llm_provider: str = None,
                   llm_model: Optional[str] = None,
                   embedding_provider: str = None,
                   embedding_model: Optional[str] = None) -> RAGPipeline:
    """
    Load or initialize the RAG pipeline with the specified models.
    Thread-safe implementation with caching.
    
    Args:
        llm_provider: Provider for the LLM
        llm_model: Optional specific LLM model
        embedding_provider: Provider for embeddings
        embedding_model: Optional specific embedding model
        
    Returns:
        Initialized RAG pipeline
        
    Raises:
        ValueError: If invalid providers are specified
        ConnectionError: If unable to connect to vector store
    """
    # Use defaults if not specified
    llm_provider = llm_provider or config.get_default_llm_provider()
    embedding_provider = embedding_provider or config.get_default_embedding_provider()
    llm_model = llm_model or config.get_default_llm_model()
    embedding_model = embedding_model or config.get_default_embedding_model()
    
    # Create cache key
    cache_key = (llm_provider, llm_model or "", embedding_provider, embedding_model or "")
    
    # Check cache first (thread-safe)
    with _cache_lock:
        if cache_key in _pipeline_cache:
            return _pipeline_cache[cache_key]
    
    try:
        # Create new pipeline
        pipeline = RAGPipeline(
            llm_provider=llm_provider,
            llm_model=llm_model,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model
        )
        
        # Cache the pipeline (thread-safe)
        with _cache_lock:
            _pipeline_cache[cache_key] = pipeline
            
        return pipeline
        
    except Exception as e:
        print(f"Error creating RAG pipeline: {str(e)}")
        raise