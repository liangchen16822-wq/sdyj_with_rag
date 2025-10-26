# RAG 集成使用说明

## 概述

RAG（检索增强生成）功能现已集成到主交互式界面中。您可以通过统一的菜单系统管理文档和执行研究任务。

## 前置要求

1. **安装依赖**：
```bash
pip install chromadb sentence-transformers
```

2. **配置 RAG**：
在项目根目录的 `config.json` 中添加 RAG 配置：

```json
{
  "rag": {
    "enabled": true,
    "collection_name": "sdyj_docs",
    "persist_directory": "./rag_data",
    "embedding_model": "text-embedding-3-small",
    "embedding_provider": "openai",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "top_k": 5
  }
}
```

**注意**：
- 如果使用 OpenAI embeddings，需要在 `.env` 中设置 `OPENAI_API_KEY`
- 如果使用 HuggingFace embeddings，设置 `embedding_provider` 为 `"huggingface"`

## 启动交互式界面

```bash
python -m SDYJ_Agents.cli.main
```

或者：

```bash
python main.py
```

## 使用 RAG 功能

### 主菜单

启动后，如果 RAG 配置正确，您会看到如下主菜单：

```
主菜单：

  1. 执行研究任务
  2. 查看可用模型
  3. 配置设置
  4. 查看当前配置
  5. RAG 文档管理  ← 新增功能
  6. 退出程序
```

### RAG 文档管理子菜单

选择 `5` 进入 RAG 文档管理，您会看到：

```
RAG 文档管理：

  1. 添加文档
  2. 添加目录
  3. 搜索文档
  4. 查看统计信息
  5. 清空所有文档
  6. 返回主菜单
```

### 功能说明

#### 1. 添加文档

- 选择 `1` 添加单个或多个文档
- 支持格式：PDF, TXT, MD, DOCX 等
- 可以一次添加多个文件（用空格分隔）

**示例**：
```
请输入文件路径（多个文件用空格分隔）：
> ./docs/paper1.pdf ./docs/paper2.pdf ./docs/notes.md
```

#### 2. 添加目录

- 选择 `2` 添加整个目录中的文档
- 支持递归搜索子目录
- 可以按文件扩展名过滤

**示例**：
```
请输入目录路径：
> ./research_papers

是否递归搜索子目录？(y/n) [y]: y

文件扩展名过滤（可选，留空表示所有支持的文件类型）：
示例: .pdf .txt .md
> .pdf .md
```

#### 3. 搜索文档

- 选择 `3` 搜索已添加的文档
- 输入自然语言查询
- 可指定返回结果数量

**示例**：
```
请输入搜索查询：
> 深度学习在自然语言处理中的应用

返回结果数量 [5]: 3
```

系统会显示最相关的文档片段及其来源和相关度评分。

#### 4. 查看统计信息

- 选择 `4` 查看 RAG 系统统计
- 显示：
  - 集合名称
  - 文档块总数
  - 嵌入模型
  - 存储目录

#### 5. 清空所有文档

- 选择 `5` 清空向量数据库
- 需要输入 `yes` 确认操作
- **警告**：此操作不可逆！

## 完整工作流示例

### 场景：研究 AI Agent 相关内容

1. **启动程序**：
```bash
python -m SDYJ_Agents.cli.main
```

2. **添加研究资料**：
```
主菜单 > 选择 5 (RAG 文档管理)
RAG 菜单 > 选择 2 (添加目录)
输入目录：./ai_agent_papers
递归搜索：y
文件扩展名：.pdf
```

3. **搜索相关文档**：
```
RAG 菜单 > 选择 3 (搜索文档)
输入查询：multi-agent systems architecture
返回结果数量：5
```

4. **返回主菜单执行研究**：
```
RAG 菜单 > 选择 6 (返回主菜单)
主菜单 > 选择 1 (执行研究任务)
输入问题：请基于我的文档，分析多智能体系统的架构设计
```

## RAG 与研究系统集成

当您执行研究任务时，系统会自动：
1. 检测 RAG 是否可用
2. 如果可用，在研究过程中会查询本地文档库
3. 将本地知识与在线搜索结果结合
4. 生成更全面、更准确的研究报告

## 故障排除

### RAG 功能不可用

如果看不到 "RAG 文档管理" 选项，请检查：

1. **依赖是否安装**：
```bash
pip list | grep chromadb
pip list | grep sentence-transformers
```

2. **配置文件是否正确**：
- 确认 `config.json` 存在于项目根目录
- 确认 `rag.enabled` 设置为 `true`

3. **API 密钥是否配置**（如果使用 OpenAI embeddings）：
```bash
# 检查 .env 文件
cat .env | grep OPENAI_API_KEY
```

### 文档添加失败

常见原因：
- 文件格式不支持
- 文件损坏或无法读取
- 嵌入服务不可用（检查 API 密钥）

### 搜索无结果

可能原因：
- 向量数据库为空（先添加文档）
- 查询与文档内容不匹配
- `top_k` 设置过小

## 命令行模式（旧方式）

如果您更喜欢使用命令行，仍然可以使用：

```bash
# 添加文档
python -m SDYJ_Agents.cli.rag_cli add 文档.pdf

# 搜索
python -m SDYJ_Agents.cli.rag_cli search "查询内容"

# 统计
python -m SDYJ_Agents.cli.rag_cli stats
```

但现在推荐使用统一的交互式界面，体验更好！

## 配置选项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `enabled` | 是否启用 RAG | `false` |
| `collection_name` | 向量集合名称 | `"default"` |
| `persist_directory` | 数据持久化目录 | `"./rag_data"` |
| `embedding_model` | 嵌入模型名称 | `"text-embedding-3-small"` |
| `embedding_provider` | 嵌入提供商 | `"openai"` |
| `chunk_size` | 文本块大小 | `1000` |
| `chunk_overlap` | 文本块重叠大小 | `200` |
| `top_k` | 默认返回结果数 | `5` |

## 支持的文件格式

- **文本文件**：.txt, .md, .markdown
- **PDF 文件**：.pdf
- **Word 文档**：.docx, .doc
- **其他格式**：根据已安装的加载器

## 最佳实践

1. **文档组织**：
   - 将相关文档放在同一目录
   - 使用有意义的文件名
   - 定期更新文档库

2. **搜索技巧**：
   - 使用具体的查询词
   - 增加 `top_k` 获取更多结果
   - 尝试不同的查询表达方式

3. **性能优化**：
   - 首次添加大量文档时需要耐心等待
   - 使用 HuggingFace embeddings 可以离线工作
   - 定期清理不需要的文档

## 反馈与支持

如有问题或建议，请提交 Issue 或 Pull Request。

祝您使用愉快！🎉

