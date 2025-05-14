import os
from pathlib import Path
from typing import Dict, Any, Optional

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS

from model_providers import get_llm_model, get_embeddings_model
from ingest import ingest_and_build

STORAGE_PATH = Path(__file__).resolve().parent / 'storage'

# Custom prompt template for knowledge base
PROMPT_TEMPLATE = """
You are a helpful assistant with access to a specific knowledge base.
Answer questions based only on the following context:

Context: {context}

Question: {query}

If the answer is not in the provided context, indicate that you don't have that information and suggest 
that the user may want to rephrase their question or check another source. Do not make up information.

Your answer should be clear, concise, and easy to understand. If there are specific requirements or procedures,
list them in an organized manner.

Answer:
"""

class RAGPipeline:
    def __init__(self, 
                 llm_provider: str = "openai", 
                 llm_model: Optional[str] = None,
                 embedding_provider: str = "openai", 
                 embedding_model: Optional[str] = None,
                 temperature: float = 0):
        """
        Initialize the RAG pipeline with configurable model providers.
        
        Args:
            llm_provider: Provider for the LLM ("openai", "ollama", "huggingface")
            llm_model: Optional specific LLM model to use
            embedding_provider: Provider for embeddings ("openai", "ollama", "huggingface")
            embedding_model: Optional specific embedding model to use
            temperature: Temperature for text generation
        """
        # Initialize embeddings model
        self.embeddings = get_embeddings_model(provider=embedding_provider, model_name=embedding_model)
        
        # Try to load local FAISS index if it exists, else build it
        if STORAGE_PATH.exists() and any(STORAGE_PATH.iterdir()):
            self.vector_store = FAISS.load_local(str(STORAGE_PATH), self.embeddings, allow_dangerous_deserialization=True)
        else:
            # Build and persist the vectorstore
            self.vector_store = ingest_and_build(
                str(STORAGE_PATH), 
                embedding_provider=embedding_provider, 
                embedding_model=embedding_model
            )

        # Create retriever
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        
        # Initialize LLM
        self.llm = get_llm_model(provider=llm_provider, model_name=llm_model, temperature=temperature)
        
        # Create prompt from template
        self.prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
        
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

# Convenience loader
_pipeline: RAGPipeline | None = None

def load_rag_chain(llm_provider: str = "openai", 
                  llm_model: Optional[str] = None,
                  embedding_provider: str = "openai", 
                  embedding_model: Optional[str] = None) -> RAGPipeline:
    """
    Load or initialize the RAG pipeline with the specified models.
    
    Args:
        llm_provider: Provider for the LLM
        llm_model: Optional specific LLM model
        embedding_provider: Provider for embeddings
        embedding_model: Optional specific embedding model
        
    Returns:
        Initialized RAG pipeline
    """
    global _pipeline
    
    # If models are changed, recreate the pipeline
    if _pipeline is not None:
        if (os.getenv("LLM_PROVIDER") != llm_provider or 
            os.getenv("EMBEDDING_PROVIDER") != embedding_provider):
            _pipeline = None
    
    if _pipeline is None:
        # Save the current configuration
        os.environ["LLM_PROVIDER"] = llm_provider
        os.environ["EMBEDDING_PROVIDER"] = embedding_provider
        if llm_model:
            os.environ["LLM_MODEL"] = llm_model
        if embedding_model:
            os.environ["EMBEDDING_MODEL"] = embedding_model
            
        _pipeline = RAGPipeline(
            llm_provider=llm_provider,
            llm_model=llm_model,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model
        )
        
    return _pipeline