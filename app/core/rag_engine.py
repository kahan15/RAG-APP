from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.vectorstores.chroma import Chroma
from langchain.chains import ConversationalRetrievalChain
from app.core.logger import setup_logger
import os
from dotenv import load_dotenv
import aiohttp
import json
import datetime
import uuid

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

class RAGEngine:
    def __init__(
        self,
        model_name: str = "deepseek-r1-distill-llama-70b",
        embedding_model: str = "sentence-transformers/all-mpnet-base-v2",
        chroma_persist_dir: str = "./data/vector_store",
        temperature: float = 0.1
    ):
        """Initialize the RAG engine with specified models and settings."""
        logger.info(f"Initializing RAG engine with model: {model_name}")
        self.model_name = model_name
        self.embedding_model = embedding_model
        self.chroma_persist_dir = Path(chroma_persist_dir)
        self.temperature = temperature
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.current_web_ids = set()  # Track current web document IDs
        self.latest_document_id = None  # Track the most recently added document
        self.document_metadata = {}  # Store metadata for each document
        
        try:
            # Initialize components
            self._init_embeddings()
            self._init_vector_store()
            self._init_llm()
            self._init_memory()
            self._init_chain()
            self._load_document_metadata()
            logger.info("RAG engine initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {str(e)}", exc_info=True)
            raise

    def _init_embeddings(self):
        """Initialize the embedding model."""
        logger.debug(f"Initializing embeddings with model: {self.embedding_model}")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'}
            )
            logger.debug("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {str(e)}", exc_info=True)
            raise

    def _init_vector_store(self):
        """Initialize the ChromaDB vector store."""
        logger.debug(f"Initializing vector store at: {self.chroma_persist_dir}")
        try:
            self.vector_store = Chroma(
                persist_directory=str(self.chroma_persist_dir),
                embedding_function=self.embeddings,
                client_settings=Settings(
                    anonymized_telemetry=False
                )
            )
            logger.debug("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
            raise

    def _init_llm(self):
        """Initialize the Groq LLM."""
        logger.debug(f"Initializing LLM with model: {self.model_name}")
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not found")
                
            self.llm = ChatGroq(
                model_name=self.model_name,
                temperature=self.temperature,
                groq_api_key=api_key
            )
            logger.debug("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}", exc_info=True)
            raise

    def _init_memory(self):
        """Initialize conversation memory."""
        logger.debug("Initializing conversation memory")
        try:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            logger.debug("Memory initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize memory: {str(e)}", exc_info=True)
            raise

    def _init_chain(self):
        """Initialize the RAG chain."""
        logger.debug("Initializing RAG chain")
        try:
            # Define the RAG prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful AI assistant powered by a RAG system. Your role is to provide accurate and relevant information from the documents provided.

                Use the following pieces of context to answer the user's question. The context has been split into chunks for better processing.
                
                Context: {context}
                
                Guidelines:
                1. If you find relevant information in the context, provide a comprehensive answer.
                2. If you're summarizing a document, combine information from all relevant chunks to create a complete summary.
                3. Always maintain the original meaning and accuracy of the source material.
                4. If you cannot find relevant information in the context, clearly state that.
                5. Cite specific parts or sections of the document when possible.
                
                Format your responses in markdown, and structure them clearly with sections when appropriate."""),
                ("human", "{question}"),
            ])

            # Initialize memory with custom input/output keys
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                input_key="question",
                output_key="answer",
                return_messages=True
            )

            # Initialize the chain with better retrieval settings
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vector_store.as_retriever(
                    search_type="mmr",  # Use MMR for better diversity in retrieved chunks
                    search_kwargs={
                        "k": 6,  # Retrieve more chunks for better context
                        "fetch_k": 10,  # Fetch more candidates for MMR
                        "lambda_mult": 0.7  # Balance between relevance and diversity
                    }
                ),
                memory=self.memory,
                combine_docs_chain_kwargs={
                    "prompt": prompt,
                    "document_variable_name": "context"
                },
                return_source_documents=True,  # Always return source documents
                return_generated_question=False,  # Don't return the generated question
                output_key="answer"  # Specify the output key to match memory
            )
            logger.debug("RAG chain initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG chain: {str(e)}", exc_info=True)
            raise

    def _load_document_metadata(self):
        """Load document metadata from disk."""
        metadata_path = self.chroma_persist_dir / "document_metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    self.document_metadata = json.load(f)
                logger.info("Successfully loaded document metadata")
            except Exception as e:
                logger.error(f"Failed to load document metadata: {str(e)}")
                self.document_metadata = {}

    def _save_document_metadata(self):
        """Save document metadata to disk."""
        metadata_path = self.chroma_persist_dir / "document_metadata.json"
        try:
            with open(metadata_path, 'w') as f:
                json.dump(self.document_metadata, f)
            logger.info("Successfully saved document metadata")
        except Exception as e:
            logger.error(f"Failed to save document metadata: {str(e)}")

    async def add_documents(
        self,
        documents: List[Document],
        source_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add documents to the vector store."""
        logger.info(f"Adding {len(documents)} documents of type: {source_type}")
        try:
            # Generate a unique document ID
            doc_id = str(uuid.uuid4())
            
            # Ensure each document has the source type and additional metadata
            for doc in documents:
                doc.metadata["source_type"] = source_type
                doc.metadata["document_id"] = doc_id
                if metadata:
                    doc.metadata.update(metadata)

            # Store document metadata
            self.document_metadata[doc_id] = {
                "source_type": source_type,
                "timestamp": str(datetime.datetime.now()),
                **(metadata or {})
            }
            self.latest_document_id = doc_id

            # Add to vector store
            self.vector_store.add_documents(documents)
            
            # Save metadata
            self._save_document_metadata()
            
            logger.info(f"Successfully added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}", exc_info=True)
            raise

    async def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search the web using Serper API."""
        logger.info(f"Searching web for: {query}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": self.serper_api_key},
                    json={"q": query}
                ) as response:
                    data = await response.json()
                    logger.debug(f"Serper API response: {data}")
                    
                    results = []
                    # Process organic search results
                    if "organic" in data:
                        for result in data["organic"][:3]:  # Get top 3 results
                            results.append({
                                "title": result.get("title", ""),
                                "snippet": result.get("snippet", ""),
                                "link": result.get("link", ""),
                                "source": "web"
                            })
                    
                    # Process knowledge graph if available
                    if "knowledgeGraph" in data:
                        kg = data["knowledgeGraph"]
                        results.append({
                            "title": kg.get("title", ""),
                            "description": kg.get("description", ""),
                            "type": "knowledge_graph",
                            "source": "web"
                        })
                    
                    logger.info(f"Found {len(results)} web results")
                    return results
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}", exc_info=True)
            return []

    def _cleanup_web_results(self):
        """Remove previous web results from the vector store."""
        try:
            if self.current_web_ids:
                # Get all documents
                all_docs = self.vector_store.get()
                if all_docs and 'ids' in all_docs:
                    # Filter out web documents
                    docs_to_keep = [
                        idx for idx in all_docs['ids']
                        if idx not in self.current_web_ids
                    ]
                    if docs_to_keep:
                        # Create new collection with non-web documents
                        self.vector_store._collection.delete(ids=list(self.current_web_ids))
                    
                # Clear the tracking set
                self.current_web_ids.clear()
                logger.info("Cleaned up previous web results")
        except Exception as e:
            logger.error(f"Error cleaning up web results: {str(e)}", exc_info=True)

    async def query(
        self,
        question: str,
        source_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the RAG system with a question."""
        logger.info(f"Processing query: {question}")
        try:
            # If source_filter specifies "latest", use the latest document ID
            if source_filter and source_filter.get("latest"):
                if self.latest_document_id:
                    source_filter = {"document_id": self.latest_document_id}
                    logger.debug(f"Using latest document ID: {self.latest_document_id}")
                else:
                    return {
                        "answer": "No documents have been uploaded yet. Please upload a document first.",
                        "sources": []
                    }

            # Configure retriever with filters
            retriever_kwargs = {
                "search_type": "mmr",
                "search_kwargs": {
                    "k": 6,
                    "fetch_k": 10,
                    "lambda_mult": 0.7
                }
            }
            
            if source_filter:
                retriever_kwargs["search_kwargs"]["filter"] = source_filter

            # Update retriever
            self.chain.retriever = self.vector_store.as_retriever(**retriever_kwargs)

            # Process the query
            result = await self.chain.ainvoke({
                "question": question
            })

            # Format the response
            response = {
                "answer": result.get("answer", ""),
                "sources": []
            }

            # Process source documents
            if "source_documents" in result:
                seen_chunks = set()  # Track unique chunks
                for doc in result["source_documents"]:
                    # Create a unique identifier for the chunk
                    chunk_id = f"{doc.metadata.get('file', '')}_{doc.metadata.get('chunk', '')}"
                    
                    if chunk_id not in seen_chunks:
                        seen_chunks.add(chunk_id)
                        source_info = {
                            "file": doc.metadata.get("file", ""),
                            "chunk": doc.metadata.get("chunk", ""),
                            "page": doc.metadata.get("page", ""),
                            "relevance": doc.metadata.get("relevance", 1.0)
                        }
                        
                        # Add document metadata if available
                        doc_id = doc.metadata.get("document_id")
                        if doc_id and doc_id in self.document_metadata:
                            source_info["metadata"] = self.document_metadata[doc_id]
                        
                        response["sources"].append(source_info)

            # Add confidence score based on source relevance
            if response["sources"]:
                avg_relevance = sum(s.get("relevance", 0) for s in response["sources"]) / len(response["sources"])
                response["confidence"] = avg_relevance
            else:
                response["confidence"] = 0.0
                if not response["answer"]:
                    response["answer"] = "I could not find any relevant information in the available documents to answer your question. Please try rephrasing your question or ensure that the relevant document has been uploaded."

            return response
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            raise

    def clear_memory(self):
        """Clear the conversation memory."""
        logger.info("Clearing conversation memory")
        try:
            self.memory.clear()
            logger.info("Memory cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear memory: {str(e)}", exc_info=True)
            raise 