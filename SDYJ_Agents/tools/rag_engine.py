"""
RAG Engine

This module provides Retrieval-Augmented Generation (RAG) functionality.
"""

import os
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib
from datetime import datetime

# 禁用 tokenizers 的并行警告
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from .document_loader import Document, DocumentLoader, TextSplitter


class RAGEngine:
    """
    RAG engine for document retrieval and augmented generation.
    """

    def __init__(
        self,
        collection_name: str = "default",
        persist_directory: str = "./rag_data",
        embedding_model: str = "text-embedding-3-small",
        embedding_provider: str = "openai",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 5
    ):
        """
        Initialize RAG engine.

        Args:
            collection_name: Name of the vector collection
            persist_directory: Directory to persist vector data
            embedding_model: Name of the embedding model
            embedding_provider: Provider for embeddings (openai, huggingface)
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            top_k: Number of top results to retrieve
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.embedding_model = embedding_model
        self.embedding_provider = embedding_provider
        self.top_k = top_k

        # Create persist directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.document_loader = DocumentLoader()
        self.text_splitter = TextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Initialize vector store
        self.vector_store = None
        self.embeddings = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize vector store and embeddings."""
        try:
            import chromadb
            from chromadb.config import Settings

            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            print(f"✓ 向量数据库已初始化: {self.collection_name}")

        except ImportError:
            raise ImportError(
                "需要安装 chromadb: pip install chromadb"
            )

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self.embedding_provider == "openai":
            return self._get_openai_embeddings(texts)
        elif self.embedding_provider == "huggingface":
            return self._get_huggingface_embeddings(texts)
        else:
            raise ValueError(f"不支持的嵌入提供商: {self.embedding_provider}")

    def _get_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from OpenAI."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Batch embed texts
            embeddings = []
            batch_size = 100  # OpenAI limit
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )
                embeddings.extend([item.embedding for item in response.data])
            
            return embeddings
            
        except ImportError:
            raise ImportError("需要安装 openai: pip install openai")
        except Exception as e:
            raise Exception(f"OpenAI 嵌入失败: {str(e)}")

    def _get_huggingface_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from HuggingFace model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            if not hasattr(self, '_hf_model'):
                self._hf_model = SentenceTransformer(self.embedding_model)
            
            embeddings = self._hf_model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
            
        except ImportError:
            raise ImportError(
                "需要安装 sentence-transformers: pip install sentence-transformers"
            )

    def add_documents(
        self,
        file_paths: List[str],
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add documents to the vector store.

        Args:
            file_paths: List of file paths to add
            metadata: Additional metadata to attach

        Returns:
            Dictionary with operation results
        """
        results = {
            'success': [],
            'failed': [],
            'total_chunks': 0
        }

        for file_path in file_paths:
            try:
                # Load document
                doc = self.document_loader.load(file_path)

                # Add custom metadata
                if metadata:
                    doc.metadata.update(metadata)

                # Split into chunks
                chunked_docs = self.text_splitter.split_documents([doc])

                # Prepare data for vector store
                texts = [chunk.content for chunk in chunked_docs]
                metadatas = [chunk.metadata for chunk in chunked_docs]

                # Generate IDs
                ids = [
                    self._generate_id(chunk.source, chunk.metadata.get('chunk_index', 0))
                    for chunk in chunked_docs
                ]

                # Get embeddings
                embeddings = self._get_embeddings(texts)

                # Add to collection
                self.collection.add(
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )

                results['success'].append(file_path)
                results['total_chunks'] += len(chunked_docs)

                print(f"✓ 已添加文档: {file_path} ({len(chunked_docs)} 个块)")

            except Exception as e:
                results['failed'].append({
                    'file_path': file_path,
                    'error': str(e)
                })
                print(f"✗ 添加文档失败 {file_path}: {str(e)}")

        return results

    def add_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add all documents from a directory.

        Args:
            directory_path: Path to directory
            recursive: Whether to search recursively
            file_extensions: List of file extensions to include
            metadata: Additional metadata

        Returns:
            Dictionary with operation results
        """
        documents = self.document_loader.load_directory(
            directory_path=directory_path,
            recursive=recursive,
            file_extensions=file_extensions
        )

        file_paths = [doc.source for doc in documents]
        return self.add_documents(file_paths, metadata)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Metadata filters

        Returns:
            List of search results with content and metadata
        """
        if top_k is None:
            top_k = self.top_k

        try:
            # Get query embedding
            query_embedding = self._get_embeddings([query])[0]

            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )

            # Format results
            formatted_results = []
            
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'id': results['ids'][0][i]
                    })

            return formatted_results

        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []

    def get_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None
    ) -> str:
        """
        Get formatted context for a query.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Metadata filters

        Returns:
            Formatted context string
        """
        results = self.search(query, top_k, filter_metadata)

        if not results:
            return "没有找到相关文档。"

        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            source = metadata.get('filename', '未知文件')
            
            context_parts.append(
                f"[来源 {i}: {source}]\n{result['content']}\n"
            )

        return "\n".join(context_parts)

    def delete_documents(
        self,
        file_path: Optional[str] = None,
        filter_metadata: Optional[Dict] = None
    ) -> int:
        """
        Delete documents from vector store.

        Args:
            file_path: Specific file path to delete
            filter_metadata: Metadata filters for deletion

        Returns:
            Number of chunks deleted
        """
        try:
            if file_path:
                # Delete by file path
                where_filter = {"file_path": str(Path(file_path).absolute())}
            elif filter_metadata:
                where_filter = filter_metadata
            else:
                raise ValueError("必须提供 file_path 或 filter_metadata")

            # Get IDs to delete
            results = self.collection.get(where=where_filter)
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                count = len(results['ids'])
                print(f"✓ 已删除 {count} 个文档块")
                return count
            
            return 0

        except Exception as e:
            print(f"删除失败: {str(e)}")
            return 0

    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✓ 已清空集合: {self.collection_name}")
        except Exception as e:
            print(f"清空集合失败: {str(e)}")

    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with statistics
        """
        try:
            count = self.collection.count()
            
            return {
                'collection_name': self.collection_name,
                'total_chunks': count,
                'embedding_model': self.embedding_model,
                'persist_directory': str(self.persist_directory)
            }
        except Exception as e:
            return {'error': str(e)}

    def _generate_id(self, source: str, chunk_index: int) -> str:
        """Generate unique ID for a document chunk."""
        content = f"{source}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()


class RAGTool:
    """
    RAG tool wrapper for integration with agent system.
    """

    def __init__(
        self,
        rag_engine: RAGEngine
    ):
        """
        Initialize RAG tool.

        Args:
            rag_engine: RAG engine instance
        """
        self.rag_engine = rag_engine

    def search_documents(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict:
        """
        Search documents and return formatted results.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Search results dictionary
        """
        results = self.rag_engine.search(query, top_k)

        return {
            'query': query,
            'source': 'rag',
            'results': [
                {
                    'content': r['content'],
                    'metadata': r['metadata'],
                    'relevance_score': 1 - r['distance'] if r['distance'] else None
                }
                for r in results
            ],
            'timestamp': datetime.now().isoformat(),
            'total_results': len(results)
        }

    def get_context_for_query(
        self,
        query: str,
        top_k: int = 5
    ) -> str:
        """
        Get formatted context for a query.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Formatted context string
        """
        return self.rag_engine.get_context(query, top_k)

