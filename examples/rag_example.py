"""
RAG 功能快速开始示例

本示例演示如何使用 RAG 功能进行文档管理和检索。
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from SDYJ_Agents.tools import RAGEngine, RAGTool


def example_basic_usage():
    """基础使用示例"""
    print("=" * 60)
    print("示例 1: 基础使用")
    print("=" * 60)
    
    # 初始化 RAG 引擎
    rag_engine = RAGEngine(
        collection_name="example_docs",
        persist_directory="./example_rag_data",
        embedding_model="text-embedding-3-small",
        embedding_provider="openai",  # 或 "huggingface"
        chunk_size=500,
        chunk_overlap=100,
        top_k=3
    )
    
    # 添加单个文档
    print("\n添加文档...")
    results = rag_engine.add_documents([
        "./README.md",
        "./project.md"
    ])
    
    print(f"✓ 成功添加 {len(results['success'])} 个文件")
    print(f"✓ 共处理 {results['total_chunks']} 个文档块")
    
    # 搜索文档
    print("\n搜索文档...")
    query = "如何使用这个项目"
    search_results = rag_engine.search(query, top_k=3)
    
    print(f"查询: {query}")
    print(f"找到 {len(search_results)} 个相关结果:\n")
    
    for i, result in enumerate(search_results, 1):
        print(f"结果 {i}:")
        print(f"  来源: {result['metadata']['filename']}")
        print(f"  相关度: {1 - result['distance']:.4f}")
        print(f"  内容预览: {result['content'][:100]}...")
        print()
    
    # 获取格式化上下文
    print("\n获取格式化上下文...")
    context = rag_engine.get_context(query, top_k=2)
    print(context)


def example_directory_loading():
    """目录加载示例"""
    print("\n" + "=" * 60)
    print("示例 2: 批量加载目录")
    print("=" * 60)
    
    rag_engine = RAGEngine(collection_name="docs_collection")
    
    # 添加整个目录
    print("\n加载目录中的所有文档...")
    results = rag_engine.add_directory(
        directory_path="./outputs",
        recursive=True,
        file_extensions=['.md', '.html']
    )
    
    print(f"✓ 成功添加 {len(results['success'])} 个文件")
    print(f"✓ 共处理 {results['total_chunks']} 个文档块")
    
    # 查看统计信息
    stats = rag_engine.get_stats()
    print("\n统计信息:")
    print(f"  集合名称: {stats['collection_name']}")
    print(f"  总文档块数: {stats['total_chunks']}")
    print(f"  嵌入模型: {stats['embedding_model']}")


def example_with_metadata():
    """使用元数据的示例"""
    print("\n" + "=" * 60)
    print("示例 3: 使用元数据过滤")
    print("=" * 60)
    
    rag_engine = RAGEngine(collection_name="filtered_docs")
    
    # 添加带有元数据的文档
    print("\n添加带元数据的文档...")
    results = rag_engine.add_documents(
        file_paths=["./README.md"],
        metadata={
            "category": "documentation",
            "language": "chinese",
            "version": "1.0"
        }
    )
    
    # 使用元数据过滤搜索
    print("\n使用元数据过滤搜索...")
    results = rag_engine.search(
        query="功能介绍",
        top_k=5,
        filter_metadata={"category": "documentation"}
    )
    
    print(f"找到 {len(results)} 个匹配的文档")


def example_rag_tool():
    """RAGTool 使用示例"""
    print("\n" + "=" * 60)
    print("示例 4: 使用 RAGTool")
    print("=" * 60)
    
    # 初始化 RAG 引擎
    rag_engine = RAGEngine(collection_name="tool_example")
    
    # 添加一些文档
    rag_engine.add_documents(["./README.md"])
    
    # 创建 RAG 工具
    rag_tool = RAGTool(rag_engine)
    
    # 使用工具进行搜索
    print("\n使用 RAGTool 搜索...")
    results = rag_tool.search_documents(
        query="项目功能",
        top_k=3
    )
    
    print(f"查询: {results['query']}")
    print(f"来源: {results['source']}")
    print(f"结果数量: {results['total_results']}")
    print(f"时间戳: {results['timestamp']}")
    
    # 获取上下文
    context = rag_tool.get_context_for_query("如何开始使用", top_k=2)
    print(f"\n上下文:\n{context}")


def example_cleanup():
    """清理示例"""
    print("\n" + "=" * 60)
    print("示例 5: 清理操作")
    print("=" * 60)
    
    rag_engine = RAGEngine(collection_name="cleanup_example")
    
    # 添加文档
    rag_engine.add_documents(["./README.md"])
    
    # 查看统计
    stats = rag_engine.get_stats()
    print(f"\n清理前: {stats['total_chunks']} 个文档块")
    
    # 删除特定文档
    print("\n删除特定文档...")
    count = rag_engine.delete_documents(file_path="./README.md")
    print(f"✓ 删除了 {count} 个文档块")
    
    # 再次查看统计
    stats = rag_engine.get_stats()
    print(f"清理后: {stats['total_chunks']} 个文档块")


if __name__ == "__main__":
    print("\nRAG 功能示例演示")
    print("=" * 60)
    
    try:
        # 运行示例（根据需要注释/取消注释）
        example_basic_usage()
        # example_directory_loading()
        # example_with_metadata()
        # example_rag_tool()
        # example_cleanup()
        
        print("\n" + "=" * 60)
        print("✓ 所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        print("\n提示:")
        print("1. 确保已安装所有依赖: pip install -r requirements.txt")
        print("2. 如果使用 OpenAI，请设置环境变量: export OPENAI_API_KEY='your-key'")
        print("3. 确保 config.json 中 rag.enabled = true")

