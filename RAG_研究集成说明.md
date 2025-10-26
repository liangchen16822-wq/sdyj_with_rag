# RAG 研究集成功能说明 🎯

## ✅ 已完成的集成

RAG 功能现已完全集成到研究流程中！

### 🔧 更新内容

1. **Researcher Agent 增强**
   - 添加了 RAG 搜索支持
   - 新增 `_search_rag()` 方法，专门处理本地文档搜索
   - RAG 结果会转换为标准格式，与其他搜索结果一起处理

2. **自动 RAG 初始化**
   - 系统启动时自动检测并加载 RAG 引擎
   - 显示文档库统计信息（文档块数量）
   - 如果 RAG 未启用或初始化失败，会显示警告但不影响其他功能

3. **研究计划自动包含 RAG**
   - Planner 现在会自动将 "rag" 添加为搜索源
   - RAG 会作为第一个搜索源，优先查询本地知识库
   - 然后再进行在线搜索（Tavily、Arxiv）

4. **参考资料中显示 RAG 结果**
   - RAG 检索到的文档会显示为"本地文档: 文件名"
   - URL 格式为 `local://文件路径`
   - 包含相关度评分

## 🚀 使用方法

### 1. 启用 RAG

编辑 `config.json`：

```json
{
  "rag": {
    "enabled": true,
    "collection_name": "default",
    "persist_directory": "./rag_data",
    "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "embedding_provider": "huggingface",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "top_k": 5
  }
}
```

### 2. 添加文档到知识库

```bash
python -m SDYJ_Agents.cli.main
# 选择 5 (RAG 文档管理)
# 选择 1 (添加文档) 或 2 (添加目录)
```

### 3. 执行研究任务

```bash
python -m SDYJ_Agents.cli.main
# 选择 1 (执行研究任务)
# 输入问题，例如："1+1等于几？"
```

系统会自动：
1. ✅ 首先搜索您的本地文档（RAG）
2. ✅ 然后搜索网络和学术论文
3. ✅ 综合所有结果生成报告
4. ✅ 在参考资料中显示所有来源

## 📊 输出示例

### 终端提示

启动时您会看到：

```
正在加载配置...
✓ RAG 引擎已加载（125 个文档块）
正在初始化 DEEPSEEK LLM...
正在初始化智能体...
正在设置研究工作流...
```

### 研究计划示例

```json
{
  "research_goal": "研究 1+1 的结果",
  "sub_tasks": [
    {
      "task_id": 1,
      "description": "搜索本地文档和网络资源",
      "search_queries": ["1+1等于几", "基础数学运算"],
      "sources": ["rag", "tavily", "arxiv"],
      "priority": 1
    }
  ]
}
```

### 报告中的参考资料

```markdown
## 参考资料

1. 本地文档: 这是一个RAG知识检索库.docx - local://path/to/file
2. Basic Arithmetic - Arxiv - http://arxiv.org/abs/...
3. Mathematical Operations - Web - https://...
```

## 🎯 您的使用案例

基于您的需求："告诉系统 1+1=3"，然后查询会使用这个信息

### 步骤：

1. **创建文档**：
   ```bash
   # 创建一个文本文件
   echo "根据我的研究，1+1=3。这是一个特殊的数学系统。" > my_math.txt
   ```

2. **添加到 RAG**：
   ```bash
   python -m SDYJ_Agents.cli.main
   # 选择 5 → 1 → 输入 my_math.txt
   ```

3. **测试查询**：
   ```bash
   python -m SDYJ_Agents.cli.main
   # 选择 1 → 输入 "1+1等于几？"
   ```

4. **查看结果**：
   系统会：
   - ✅ 首先从您的本地文档中找到 "1+1=3" 的信息
   - ✅ 也会从网络搜索到 "1+1=2" 的标准答案
   - ✅ 在报告中同时展示两种来源
   - ✅ **重要**：由于 RAG 搜索在前，本地知识会被优先考虑

## 📝 技术细节

### RAG 搜索参数

- **top_k**: 10（研究时返回更多结果）
- **搜索时机**: 每个搜索查询都会同时查询 RAG
- **结果格式**: 与其他搜索源统一，便于处理

### 结果优先级

```python
sources = ["rag", "tavily", "arxiv"]  # RAG 排在第一位
```

RAG 的搜索结果会首先被处理，在生成报告时获得更高权重。

### 相关度评分

RAG 结果包含相关度评分：
```python
relevance_score = 1 - distance  # 距离越小，相关度越高
```

## 🔍 验证 RAG 是否工作

### 方法 1：查看启动信息

```
✓ RAG 引擎已加载（XXX 个文档块）
```

如果看到这行，说明 RAG 已加载。

### 方法 2：查看研究计划

在"等待您的决策"时，检查计划中的 sources 是否包含 "rag"。

### 方法 3：查看最终报告

在"参考资料"部分，查找：
```
X. 本地文档: 文件名 - local://...
```

## ⚠️ 常见问题

### Q: RAG 没有被使用？

**检查清单**：
1. ✅ `config.json` 中 `rag.enabled = true`
2. ✅ 已添加文档到 RAG
3. ✅ 启动时看到 "RAG 引擎已加载"
4. ✅ 文档内容与查询相关

### Q: 为什么还是回答标准答案？

RAG 只是提供**额外的上下文**，最终答案由 LLM 综合判断：
- 如果 RAG 文档和网络资源冲突，LLM 会考虑来源可信度
- 您可以在查询时明确指出："根据我的文档..."

### Q: 如何让 RAG 结果权重更高？

1. **在查询中明确指出**：
   ```
   "根据我的本地知识库，1+1等于几？"
   ```

2. **增加 RAG 的 top_k**：
   在 `config.json` 中：
   ```json
   {
     "rag": {
       "top_k": 20
     }
   }
   ```

3. **确保文档质量**：
   - 文档内容清晰
   - 与查询高度相关
   - 使用明确的表述

## 🎉 完成！

现在您的系统已经完全集成了 RAG 功能。每次研究都会：

1. 🔍 先搜索您的本地知识库
2. 🌐 再搜索互联网和学术论文
3. 📝 综合生成专业报告
4. 📚 在参考资料中标注所有来源

**享受您的智能研究助手吧！** 🚀

