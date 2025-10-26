# RAG 功能使用说明

本项目已集成 RAG（检索增强生成）功能，允许您读取本地文件并进行智能检索，以增强 AI 的回答质量。

## 功能特性

✅ **多格式支持**: PDF、DOCX、TXT、Markdown、HTML 等
✅ **智能分块**: 自动将长文档分割成合适的块
✅ **向量检索**: 使用向量相似度进行语义搜索
✅ **持久化存储**: 文档向量本地持久化，无需重复处理
✅ **灵活配置**: 支持多种嵌入模型和向量数据库

## 安装依赖

首先安装 RAG 所需的依赖：

```bash
pip install -r requirements.txt
```

## 配置

在 `config.json` 中配置 RAG 参数：

```json
{
  "rag": {
    "enabled": true,                          // 启用 RAG 功能
    "collection_name": "default",             // 集合名称
    "persist_directory": "./rag_data",        // 向量数据存储目录
    "embedding_model": "text-embedding-3-small",  // 嵌入模型
    "embedding_provider": "openai",           // 嵌入提供商: openai 或 huggingface
    "chunk_size": 1000,                       // 文本块大小（字符数）
    "chunk_overlap": 200,                     // 块之间重叠大小
    "top_k": 5                                // 检索返回的结果数量
  }
}
```

### 嵌入提供商选项

#### 1. OpenAI（推荐）
```json
"embedding_provider": "openai",
"embedding_model": "text-embedding-3-small"
```

需要设置环境变量：
```bash
export OPENAI_API_KEY="your-api-key"
```

#### 2. HuggingFace（本地）
```json
"embedding_provider": "huggingface",
"embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

首次使用会自动下载模型到本地。

## 使用方法

### 方法一：命令行工具

#### 1. 添加单个文件
```bash
python -m SDYJ_Agents.cli.rag_cli add document.pdf
```

#### 2. 添加多个文件
```bash
python -m SDYJ_Agents.cli.rag_cli add file1.pdf file2.txt file3.docx
```

#### 3. 添加整个目录
```bash
# 递归添加目录中的所有支持文件
python -m SDYJ_Agents.cli.rag_cli add-dir ./documents

# 只添加特定扩展名的文件
python -m SDYJ_Agents.cli.rag_cli add-dir ./documents --extensions .pdf .txt

# 不递归搜索子目录
python -m SDYJ_Agents.cli.rag_cli add-dir ./documents --no-recursive
```

#### 4. 搜索文档
```bash
python -m SDYJ_Agents.cli.rag_cli search "人工智能的应用"

# 返回更多结果
python -m SDYJ_Agents.cli.rag_cli search "深度学习" --top-k 10
```

#### 5. 查看统计信息
```bash
python -m SDYJ_Agents.cli.rag_cli stats
```

#### 6. 清空所有文档
```bash
python -m SDYJ_Agents.cli.rag_cli clear
```

### 方法二：Python API

```python
from SDYJ_Agents.tools import RAGEngine, RAGTool

# 初始化 RAG 引擎
rag_engine = RAGEngine(
    collection_name="my_documents",
    persist_directory="./my_rag_data",
    embedding_model="text-embedding-3-small",
    embedding_provider="openai",
    chunk_size=1000,
    chunk_overlap=200,
    top_k=5
)

# 添加文档
results = rag_engine.add_documents([
    "./documents/report.pdf",
    "./documents/article.txt"
])

# 添加目录
results = rag_engine.add_directory(
    directory_path="./documents",
    recursive=True,
    file_extensions=['.pdf', '.txt', '.md']
)

# 搜索
results = rag_engine.search(
    query="人工智能的发展趋势",
    top_k=5
)

for result in results:
    print(f"内容: {result['content']}")
    print(f"来源: {result['metadata']['filename']}")
    print(f"相关度: {1 - result['distance']}")
    print("---")

# 获取格式化的上下文
context = rag_engine.get_context(
    query="机器学习算法",
    top_k=3
)
print(context)

# 查看统计信息
stats = rag_engine.get_stats()
print(f"总文档块数: {stats['total_chunks']}")

# 删除特定文档
rag_engine.delete_documents(file_path="./documents/old_report.pdf")

# 清空所有文档
rag_engine.clear_collection()
```

### 方法三：集成到 Agent 系统

```python
from SDYJ_Agents.tools import RAGEngine, RAGTool

# 初始化 RAG
rag_engine = RAGEngine(
    collection_name="research_docs",
    embedding_provider="openai"
)

# 添加研究文档
rag_engine.add_directory("./research_papers")

# 创建 RAG 工具
rag_tool = RAGTool(rag_engine)

# 在 researcher agent 中使用
def research_with_rag(query: str):
    # 先从本地文档检索
    rag_results = rag_tool.search_documents(query, top_k=5)
    
    # 如果没有找到相关文档，使用网络搜索
    if not rag_results['results']:
        # 使用 Tavily 或 arXiv 搜索
        pass
    
    # 获取上下文
    context = rag_tool.get_context_for_query(query, top_k=3)
    
    # 将上下文提供给 LLM
    return context
```

## 支持的文件格式

| 格式 | 扩展名 | 依赖库 |
|------|--------|--------|
| 文本文件 | `.txt` | 内置 |
| Markdown | `.md`, `.markdown` | 内置 |
| PDF | `.pdf` | PyPDF2 |
| Word 文档 | `.docx` | python-docx |
| HTML | `.html`, `.htm` | beautifulsoup4 |

## 最佳实践

### 1. 文档组织
- 按主题或项目创建不同的集合（collection）
- 定期清理过时的文档

### 2. 分块参数调优
- **小文档**（如邮件）：`chunk_size=500, chunk_overlap=50`
- **中等文档**（如文章）：`chunk_size=1000, chunk_overlap=200`（默认）
- **大文档**（如书籍）：`chunk_size=2000, chunk_overlap=400`

### 3. 检索优化
- 使用清晰、具体的查询语句
- 根据需求调整 `top_k` 参数
- 使用元数据过滤来缩小搜索范围

### 4. 性能优化
- 首选 OpenAI 嵌入（速度快、质量高）
- 本地部署可使用 HuggingFace 模型
- 批量添加文档以提高效率

## 常见问题

### Q1: 如何切换嵌入模型？
A: 修改 `config.json` 中的 `embedding_model` 和 `embedding_provider`，然后重新添加文档。

### Q2: 向量数据存储在哪里？
A: 存储在 `persist_directory` 指定的目录中（默认 `./rag_data`）。

### Q3: 如何处理大量文档？
A: 使用 `add_directory` 命令批量添加，系统会自动处理进度。

### Q4: 支持中文吗？
A: 完全支持中文。建议使用：
- OpenAI: `text-embedding-3-small` 或 `text-embedding-3-large`
- HuggingFace: `paraphrase-multilingual-MiniLM-L12-v2`

### Q5: 如何提高检索准确度？
A: 
- 使用更大的嵌入模型（如 `text-embedding-3-large`）
- 优化文档的分块大小
- 增加 `top_k` 值获取更多候选结果
- 确保文档质量和相关性

## 示例场景

### 场景 1: 研究助手
```bash
# 添加所有研究论文
python -m SDYJ_Agents.cli.rag_cli add-dir ./research_papers --extensions .pdf

# 搜索相关论文
python -m SDYJ_Agents.cli.rag_cli search "transformer架构的优化方法"
```

### 场景 2: 文档问答
```python
rag_engine = RAGEngine(collection_name="company_docs")
rag_engine.add_directory("./company_documents")

# 回答基于文档的问题
context = rag_engine.get_context("公司的休假政策是什么？")
# 将 context 提供给 LLM 生成答案
```

### 场景 3: 知识库管理
```python
# 创建不同主题的知识库
tech_kb = RAGEngine(collection_name="tech_docs")
business_kb = RAGEngine(collection_name="business_docs")

tech_kb.add_directory("./tech_docs")
business_kb.add_directory("./business_docs")

# 分别搜索
tech_results = tech_kb.search("API设计")
business_results = business_kb.search("市场策略")
```

## 进阶使用

### 自定义元数据
```python
# 添加自定义元数据
rag_engine.add_documents(
    file_paths=["report.pdf"],
    metadata={
        "author": "张三",
        "department": "研发部",
        "date": "2024-01-01"
    }
)

# 使用元数据过滤搜索
results = rag_engine.search(
    query="项目进展",
    filter_metadata={"department": "研发部"}
)
```

### 与现有 Agent 集成
```python
# 在 researcher.py 中集成 RAG
from SDYJ_Agents.tools import RAGEngine

class Researcher:
    def __init__(self):
        self.rag_engine = RAGEngine()
        # ... 其他初始化
    
    def search(self, query: str):
        # 先搜索本地文档
        local_results = self.rag_engine.search(query, top_k=3)
        
        # 再使用网络搜索补充
        web_results = self.tavily_search.search(query)
        
        # 合并结果
        return self._merge_results(local_results, web_results)
```

## 技术架构

```
文档 → DocumentLoader → 加载
              ↓
         TextSplitter → 分块
              ↓
         Embedding API → 向量化
              ↓
         ChromaDB → 存储
              ↓
         搜索查询 → 向量检索
              ↓
         返回相关文档 → 增强生成
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 RAG 功能！

