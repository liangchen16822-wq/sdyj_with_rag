"""
Researcher Agent

This module implements the Researcher agent, which is responsible for
executing information retrieval tasks.
"""

from typing import Dict, List, Optional
from ..workflow.state import ResearchState, SubTask, SearchResult
from ..tools.tavily_search import TavilySearch
from ..tools.arxiv_search import ArxivSearch
from ..tools.mcp_client import MCPClient
from ..llm.base import BaseLLM
from ..prompts.loader import PromptLoader

# Try to import RAG engine
try:
    from ..tools.rag_engine import RAGEngine
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


class Researcher:
    """
    Researcher agent - information collection component.

    Responsibilities:
    - Execute information retrieval tasks
    - Search from multiple data sources
    - Filter and organize search results
    - Aggregate results from different sources
    - Extract relevant information
    """

    def __init__(
        self,
        llm: BaseLLM,
        tavily_api_key: Optional[str] = None,
        mcp_server_url: Optional[str] = None,
        mcp_api_key: Optional[str] = None,
        rag_engine: Optional['RAGEngine'] = None
    ):
        """
        Initialize the Researcher.

        Args:
            llm: Language model instance for processing
            tavily_api_key: Tavily API key (optional)
            mcp_server_url: MCP server URL (optional)
            mcp_api_key: MCP API key (optional)
            rag_engine: RAG engine instance for local document search (optional)
        """
        self.llm = llm
        self.tavily = TavilySearch(tavily_api_key) if tavily_api_key else None
        self.arxiv = ArxivSearch()
        self.mcp = MCPClient(mcp_server_url, mcp_api_key) if mcp_server_url else None
        self.rag = rag_engine
        self.prompt_loader = PromptLoader()

    def execute_task(self, state: ResearchState, task: SubTask) -> ResearchState:
        """
        Execute a research task.

        Args:
            state: Current research state
            task: Task to execute

        Returns:
            Updated state with research results
        """
        results = []

        # Execute searches for each query
        for query in task.get('search_queries', []):
            for source in task.get('sources', []):
                result = self._search(query, source)
                if result:
                    result['task_id'] = task['task_id']
                    results.append(result)

        # Add results to state
        if 'research_results' not in state:
            state['research_results'] = []

        state['research_results'].extend(results)

        # Mark task as completed
        if state.get('research_plan'):
            for t in state['research_plan'].get('sub_tasks', []):
                if t.get('task_id') == task['task_id']:
                    t['status'] = 'completed'
                    break

        return state

    def _search(self, query: str, source: str) -> Optional[SearchResult]:
        """
        Perform search using specified source.

        Args:
            query: Search query
            source: Source name ('tavily', 'arxiv', 'mcp', 'rag')

        Returns:
            Search results or None
        """
        try:
            if source == 'tavily' and self.tavily:
                return self.tavily.search(query)
            elif source == 'arxiv':
                return self.arxiv.search(query)
            elif source == 'mcp' and self.mcp:
                import asyncio
                return asyncio.run(self.mcp.search(query))
            elif source == 'rag' and self.rag:
                return self._search_rag(query)
            else:
                return None
        except Exception as e:
            return {
                'query': query,
                'source': source,
                'results': [],
                'error': str(e)
            }
    
    def _search_rag(self, query: str) -> SearchResult:
        """
        Search local documents using RAG.

        Args:
            query: Search query

        Returns:
            Search results in standard format
        """
        try:
            # Search RAG with higher top_k for research
            rag_results = self.rag.search(query, top_k=10)
            
            # Convert RAG results to standard format
            formatted_results = []
            for i, result in enumerate(rag_results, 1):
                metadata = result.get('metadata', {})
                formatted_results.append({
                    'title': f"本地文档: {metadata.get('filename', '未知文件')}",
                    'content': result.get('content', ''),
                    'url': f"local://{metadata.get('file_path', '')}",
                    'relevance_score': 1 - result.get('distance', 0) if result.get('distance') else None,
                    'source': 'rag',
                    'metadata': metadata
                })
            
            return {
                'query': query,
                'source': 'rag',
                'results': formatted_results,
                'total_results': len(formatted_results)
            }
        except Exception as e:
            return {
                'query': query,
                'source': 'rag',
                'results': [],
                'error': str(e)
            }

    def aggregate_results(self, results: List[SearchResult]) -> Dict:
        """
        Aggregate and organize search results.

        Args:
            results: List of search results

        Returns:
            Aggregated results summary
        """
        # Group results by source
        by_source = {}
        for result in results:
            source = result.get('source', 'unknown')
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(result)

        # Calculate statistics
        total_results = sum(len(r.get('results', [])) for r in results)

        return {
            'total_searches': len(results),
            'total_results': total_results,
            'by_source': {
                source: {
                    'count': len(source_results),
                    'total_items': sum(len(r.get('results', [])) for r in source_results)
                }
                for source, source_results in by_source.items()
            }
        }

    def extract_relevant_info(self, state: ResearchState) -> str:
        """
        Extract relevant information from all research results.

        Args:
            state: Current research state

        Returns:
            Extracted and summarized information
        """
        results = state.get('research_results', [])

        if not results:
            return "No research results available."

        # Compile all search results
        all_items = []
        for result in results:
            for item in result.get('results', []):
                all_items.append({
                    'source': result.get('source'),
                    'query': result.get('query'),
                    'title': item.get('title'),
                    'snippet': item.get('snippet'),
                    'url': item.get('url')
                })

        # Use LLM to extract and summarize
        prompt = self.prompt_loader.load(
            'researcher_extract_info',
            query=state['query'],
            search_results=self._format_results_for_prompt(all_items[:20])  # Limit to top 20 results
        )

        summary = self.llm.generate(prompt, temperature=0.5)
        return summary

    def _format_results_for_prompt(self, items: List[Dict]) -> str:
        """
        Format search results for LLM prompt.

        Args:
            items: List of search result items

        Returns:
            Formatted string
        """
        formatted = []
        for i, item in enumerate(items, 1):
            formatted.append(f"\n{i}. [{item.get('source')}] {item.get('title', 'No title')}")
            formatted.append(f"   URL: {item.get('url', 'N/A')}")
            formatted.append(f"   {item.get('snippet', 'No snippet')[:200]}...")

        return '\n'.join(formatted)

    def __repr__(self) -> str:
        """String representation."""
        sources = []
        if self.tavily:
            sources.append('tavily')
        if self.arxiv:
            sources.append('arxiv')
        if self.mcp:
            sources.append('mcp')
        return f"Researcher(sources={sources})"
