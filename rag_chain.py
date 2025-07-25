import os
from pathlib import Path
from typing import Dict, Any, Optional, List

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
        print(f"LLM provider: {llm_provider}")
        print(f"LLM model: {llm_model}")
        print(f"Embedding provider: {embedding_provider}")
        print(f"Embedding model: {embedding_model}")
        print(f"Temperature: {temperature}")
        
        # Initialize embeddings model
        self.embeddings = get_embeddings_model(provider=embedding_provider, model_name=embedding_model)
        print(f"Embeddings model: {self.embeddings}")
        
        # Get Qdrant configuration
        qdrant_url = config.get('vector_store', {}).get('qdrant_url', 'http://localhost:6333')
        collection_name = config.get('vector_store', {}).get('qdrant_collection_name', 'my_collection')
        print(f"Qdrant URL: {qdrant_url}")
        print(f"Collection name: {collection_name}")
        
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
        search_type = config.get_search_type()
        search_kwargs = {"k": config.get_top_k_results()}
        
        # Add MMR-specific parameters if using MMR search
        if search_type == "mmr":
            search_kwargs["lambda_mult"] = config.get_mmr_diversity_score()
        
        self.retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
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

    def format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """Format chat history for inclusion in the prompt."""
        if not chat_history:
            return ""
        
        formatted_history = []
        for interaction in chat_history:
            role = interaction.get('role', '')
            content = interaction.get('content', '')
            
            if role == 'user':
                formatted_history.append(f"Human: {content}")
            elif role == 'assistant':
                formatted_history.append(f"Assistant: {content}")
        
        return "\n".join(formatted_history)

    def rewrite_query_with_history(self, question: str, chat_history: List[Dict[str, str]]) -> str:
        """Rewrite the user's question to include context from chat history."""
        if not chat_history:
            return question
        
        try:
            # Format chat history for the rewrite prompt
            history_text = self.format_chat_history(chat_history)
            
            # Get the query rewrite template
            rewrite_template = config.get_query_rewrite_template()
            if not rewrite_template:
                # Fallback if no template is configured
                return question
            
            # Create the rewrite prompt
            rewrite_prompt = PromptTemplate.from_template(rewrite_template)
            
            # Create a chain for query rewriting
            rewrite_chain = (
                rewrite_prompt
                | self.llm
                | StrOutputParser()
            )
            
            # Generate the rewritten query
            rewritten_query = rewrite_chain.invoke({
                "chat_history": history_text,
                "current_question": question
            })
            
            # Clean up the response (remove any extra formatting)
            rewritten_query = rewritten_query.strip()
            
            print(f"Original query: {question}")
            print(f"Rewritten query: {rewritten_query}")
            
            return rewritten_query
            
        except Exception as e:
            print(f"Error rewriting query: {str(e)}. Using original question.")
            return question

    def __call__(self, question: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        if chat_history is None:
            chat_history = []
            
        try:
            # Rewrite the query to include context from chat history
            retrieval_query = self.rewrite_query_with_history(question, chat_history)
            
            # Get the documents from the retriever using the rewritten query
            retrieved_docs = self.retriever.get_relevant_documents(retrieval_query)
            
            # Format context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            
            # Format chat history
            history_text = self.format_chat_history(chat_history)
            
            # Create the full prompt with chat history
            prompt_input = {
                "query": question,
                "context": context
            }

            print(f"Prompt input: {prompt_input}")
            print(f"History text: {history_text}")
            print(f"Context: {context}")
            
            # If we have chat history, we need to modify the prompt to include it
            if history_text:
                # Get the original prompt template
                original_template = config.get_rag_prompt_template()
                
                # Create a new template that includes chat history
                enhanced_template = f"""Previous conversation:
{history_text}

{original_template}"""
                
                enhanced_prompt = PromptTemplate.from_template(enhanced_template)
                
                # Create a new chain with the enhanced prompt
                enhanced_chain = (
                    enhanced_prompt
                    | self.llm
                    | StrOutputParser()
                )
                
                answer = enhanced_chain.invoke(prompt_input)
            else:
                # Use the original chain if no history
                answer = self.chain.invoke(question)
            
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