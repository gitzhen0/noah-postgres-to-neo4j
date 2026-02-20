#!/usr/bin/env python3
"""
Test Text2Cypher Functionality

测试自然语言到 Cypher 的翻译功能
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import Neo4jConnection
from noah_converter.text2cypher import Text2CypherTranslator

print("=" * 70)
print("🤖 Testing Text2Cypher Translation")
print("=" * 70)

# 加载配置
config = load_config()

# 检查是否有 API key（优先 OpenAI，fallback 到 Claude）
openai_key = os.getenv('OPENAI_API_KEY')
claude_key = os.getenv('ANTHROPIC_API_KEY')

if openai_key:
    llm_provider = "openai"
    api_key = openai_key
    model = "gpt-3.5-turbo"
    print("\n✓ Using OpenAI (gpt-3.5-turbo)")
elif claude_key:
    llm_provider = "claude"
    api_key = claude_key
    model = "claude-sonnet-4-5-20250929"
    print("\n✓ Using Claude (Sonnet 4.5)")
else:
    print("\n❌ Error: No API key found")
    print("\nPlease set one of:")
    print("  export OPENAI_API_KEY='your-openai-key'")
    print("  export ANTHROPIC_API_KEY='your-anthropic-key'")
    sys.exit(1)

# 连接 Neo4j
neo4j_conn = Neo4jConnection(config.target_db)

# 创建 Text2Cypher translator
print(f"\n🔧 Initializing Text2Cypher translator with {llm_provider}...")
translator = Text2CypherTranslator(
    neo4j_conn=neo4j_conn,
    llm_provider=llm_provider,
    api_key=api_key,
    model=model,
    temperature=0
)

# 测试连接
if translator.test_connection():
    print("   ✓ Neo4j connection successful")
else:
    print("   ❌ Neo4j connection failed")
    sys.exit(1)

# 显示 schema 摘要
print("\n📊 Database Schema:")
print(translator.get_schema_summary())

# ============================================================
# 测试查询
# ============================================================

test_questions = [
    # Simple queries
    "Which ZIP codes are neighbors of 10001?",
    "Show me all housing projects in ZIP code 11106",
    "How many housing projects are in each borough?",

    # Spatial queries
    "Find ZIP codes within 5km of 10001",

    # Multi-hop queries
    "Find all ZIP codes within 2 hops of 10001",

    # Aggregate queries
    "Which borough has the most affordable housing units?",
]

print("\n" + "=" * 70)
print("🧪 Testing Queries")
print("=" * 70)

for i, question in enumerate(test_questions, 1):
    print(f"\n{'─' * 70}")
    print(f"Question {i}: {question}")
    print("─" * 70)

    try:
        # 执行查询
        result = translator.query(
            question=question,
            execute=True,
            explain=True
        )

        if result['error']:
            print(f"\n❌ Error: {result['error']}")
            continue

        # 显示生成的 Cypher
        print(f"\n📝 Generated Cypher:")
        print(f"{result['cypher']}")

        # 显示结果
        print(f"\n📊 Results ({len(result['results'])} rows):")
        if result['results']:
            # 显示前 5 条结果
            for j, record in enumerate(result['results'][:5], 1):
                print(f"   {j}. {record}")

            if len(result['results']) > 5:
                print(f"   ... and {len(result['results']) - 5} more")
        else:
            print("   (No results)")

        # 显示解释
        if result['explanation']:
            print(f"\n💬 Explanation:")
            print(f"   {result['explanation']}")

    except Exception as e:
        print(f"\n❌ Error: {e}")

# ============================================================
# 准确率统计
# ============================================================

print("\n" + "=" * 70)
print("📈 Summary")
print("=" * 70)
print(f"\nTotal questions tested: {len(test_questions)}")
print("\nNext steps:")
print("  1. Review generated Cypher queries for correctness")
print("  2. Run benchmark tests with 20+ questions")
print("  3. Calculate accuracy rate (target: >75%)")
print("=" * 70)

# 清理
neo4j_conn.close()
