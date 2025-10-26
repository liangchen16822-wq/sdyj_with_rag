"""
RAG CLI

Command-line interface for RAG operations.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from SDYJ_Agents.tools.rag_engine import RAGEngine
from SDYJ_Agents.utils.config import load_config


console = Console()


class RAGCLI:
    """
    RAG command-line interface.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize RAG CLI.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.rag_config = self.config.get('rag', {})
        
        # Initialize RAG engine if enabled
        if self.rag_config.get('enabled', False):
            self.rag_engine = self._initialize_rag()
        else:
            self.rag_engine = None

    def _initialize_rag(self) -> Optional[RAGEngine]:
        """Initialize RAG engine from config."""
        try:
            return RAGEngine(
                collection_name=self.rag_config.get('collection_name', 'default'),
                persist_directory=self.rag_config.get('persist_directory', './rag_data'),
                embedding_model=self.rag_config.get('embedding_model', 'text-embedding-3-small'),
                embedding_provider=self.rag_config.get('embedding_provider', 'openai'),
                chunk_size=self.rag_config.get('chunk_size', 1000),
                chunk_overlap=self.rag_config.get('chunk_overlap', 200),
                top_k=self.rag_config.get('top_k', 5)
            )
        except Exception as e:
            console.print(f"[red]初始化 RAG 引擎失败: {str(e)}[/red]")
            return None

    def add_documents(self, file_paths: list[str], metadata: Optional[dict] = None):
        """
        Add documents to RAG.

        Args:
            file_paths: List of file paths to add
            metadata: Optional metadata
        """
        if not self.rag_engine:
            console.print("[red]RAG 功能未启用。请在 config.json 中设置 rag.enabled = true[/red]")
            return

        console.print(f"[cyan]正在添加 {len(file_paths)} 个文档...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("处理中...", total=len(file_paths))

            results = self.rag_engine.add_documents(file_paths, metadata)

            progress.update(task, completed=len(file_paths))

        # Display results
        console.print(f"\n[green]✓ 成功添加: {len(results['success'])} 个文件[/green]")
        console.print(f"[green]✓ 总共处理: {results['total_chunks']} 个文档块[/green]")

        if results['failed']:
            console.print(f"\n[red]✗ 失败: {len(results['failed'])} 个文件[/red]")
            for failed in results['failed']:
                console.print(f"  [red]- {failed['file_path']}: {failed['error']}[/red]")

    def add_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_extensions: Optional[list[str]] = None
    ):
        """
        Add all documents from a directory.

        Args:
            directory_path: Path to directory
            recursive: Whether to search recursively
            file_extensions: List of file extensions to include
        """
        if not self.rag_engine:
            console.print("[red]RAG 功能未启用。请在 config.json 中设置 rag.enabled = true[/red]")
            return

        console.print(f"[cyan]正在扫描目录: {directory_path}[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("处理中...", total=None)

            results = self.rag_engine.add_directory(
                directory_path=directory_path,
                recursive=recursive,
                file_extensions=file_extensions
            )

            progress.update(task, completed=1)

        # Display results
        console.print(f"\n[green]✓ 成功添加: {len(results['success'])} 个文件[/green]")
        console.print(f"[green]✓ 总共处理: {results['total_chunks']} 个文档块[/green]")

        if results['failed']:
            console.print(f"\n[red]✗ 失败: {len(results['failed'])} 个文件[/red]")
            for failed in results['failed']:
                console.print(f"  [red]- {failed['file_path']}: {failed['error']}[/red]")

    def search(self, query: str, top_k: int = 5):
        """
        Search documents.

        Args:
            query: Search query
            top_k: Number of results
        """
        if not self.rag_engine:
            console.print("[red]RAG 功能未启用。请在 config.json 中设置 rag.enabled = true[/red]")
            return

        console.print(f"\n[cyan]搜索查询: {query}[/cyan]\n")

        results = self.rag_engine.search(query, top_k)

        if not results:
            console.print("[yellow]没有找到相关文档。[/yellow]")
            return

        # Display results
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            source = metadata.get('filename', '未知文件')
            
            panel = Panel(
                result['content'],
                title=f"[bold cyan]结果 {i}: {source}[/bold cyan]",
                subtitle=f"相关度: {1 - result['distance']:.4f}" if result['distance'] else "",
                border_style="cyan"
            )
            console.print(panel)
            console.print()

    def show_stats(self):
        """Show RAG statistics."""
        if not self.rag_engine:
            console.print("[red]RAG 功能未启用。请在 config.json 中设置 rag.enabled = true[/red]")
            return

        stats = self.rag_engine.get_stats()

        table = Table(title="RAG 统计信息", show_header=True, header_style="bold magenta")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="green")

        table.add_row("集合名称", stats.get('collection_name', 'N/A'))
        table.add_row("文档块总数", str(stats.get('total_chunks', 0)))
        table.add_row("嵌入模型", stats.get('embedding_model', 'N/A'))
        table.add_row("存储目录", stats.get('persist_directory', 'N/A'))

        console.print(table)

    def clear_collection(self):
        """Clear all documents from collection."""
        if not self.rag_engine:
            console.print("[red]RAG 功能未启用。请在 config.json 中设置 rag.enabled = true[/red]")
            return

        console.print("[yellow]警告: 这将删除所有文档！[/yellow]")
        confirm = input("确认删除所有文档? (yes/no): ")

        if confirm.lower() == 'yes':
            self.rag_engine.clear_collection()
            console.print("[green]✓ 已清空所有文档[/green]")
        else:
            console.print("[yellow]操作已取消[/yellow]")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="RAG 命令行工具")
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="配置文件路径"
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # Add documents command
    add_parser = subparsers.add_parser("add", help="添加文档")
    add_parser.add_argument("files", nargs="+", help="要添加的文件路径")

    # Add directory command
    add_dir_parser = subparsers.add_parser("add-dir", help="添加目录中的所有文档")
    add_dir_parser.add_argument("directory", help="目录路径")
    add_dir_parser.add_argument("--no-recursive", action="store_true", help="不递归搜索")
    add_dir_parser.add_argument(
        "--extensions",
        nargs="+",
        help="要包含的文件扩展名 (e.g., .pdf .txt)"
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="搜索文档")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("--top-k", type=int, default=5, help="返回结果数量")

    # Stats command
    subparsers.add_parser("stats", help="显示统计信息")

    # Clear command
    subparsers.add_parser("clear", help="清空所有文档")

    args = parser.parse_args()

    # Initialize CLI
    cli = RAGCLI(config_path=args.config)

    # Execute command
    if args.command == "add":
        cli.add_documents(args.files)
    elif args.command == "add-dir":
        cli.add_directory(
            args.directory,
            recursive=not args.no_recursive,
            file_extensions=args.extensions
        )
    elif args.command == "search":
        cli.search(args.query, args.top_k)
    elif args.command == "stats":
        cli.show_stats()
    elif args.command == "clear":
        cli.clear_collection()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

