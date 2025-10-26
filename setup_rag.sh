#!/bin/bash

# RAG 功能安装脚本

echo "=================================="
echo "  RAG 功能安装脚本"
echo "=================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
python_version=$(python3 --version 2>&1 | sed -E 's/Python ([0-9]+\.[0-9]+).*/\1/')
required_version="3.8"

if [ -z "$python_version" ]; then
    echo "❌ 未找到 Python 3，请先安装 Python 3.8 或更高版本"
    exit 1
fi

echo "✓ Python 版本: $python_version"
echo ""

# 安装依赖
echo "安装 RAG 相关依赖..."
echo "这可能需要几分钟时间..."
echo ""

# 使用 python3 -m pip 确保安装到正确的 Python 版本
python3 -m pip install --user chromadb>=0.4.0 \
    PyPDF2>=3.0.0 \
    python-docx>=1.1.0 \
    beautifulsoup4>=4.12.0 \
    sentence-transformers>=2.2.0 \
    lxml

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 依赖安装完成"
else
    echo ""
    echo "❌ 依赖安装失败，请检查网络连接或手动安装"
    exit 1
fi

# 创建 RAG 数据目录
echo ""
echo "创建 RAG 数据目录..."
mkdir -p rag_data
mkdir -p examples
echo "✓ 目录创建完成"

# 配置提示
echo ""
echo "=================================="
echo "  安装完成！"
echo "=================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 配置 API 密钥（如果使用 OpenAI 嵌入）："
echo "   export OPENAI_API_KEY='your-api-key'"
echo ""
echo "2. 在 config.json 中启用 RAG："
echo "   \"rag\": {"
echo "     \"enabled\": true,"
echo "     ..."
echo "   }"
echo ""
echo "3. 开始使用："
echo "   # 添加文档"
echo "   python -m SDYJ_Agents.cli.rag_cli add your_document.pdf"
echo ""
echo "   # 搜索文档"
echo "   python -m SDYJ_Agents.cli.rag_cli search \"你的查询\""
echo ""
echo "   # 查看统计信息"
echo "   python -m SDYJ_Agents.cli.rag_cli stats"
echo ""
echo "详细使用说明请查看: RAG_使用说明.md"
echo ""

