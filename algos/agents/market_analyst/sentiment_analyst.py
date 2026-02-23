from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Literal


# ============================================================
# 1. Schema 定义
# ============================================================

class ClusterSentimentAnalysis(BaseModel):
    overview: str = Field(
        ...,
        description="200字以内的行业舆情概览"
    )

    sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        ...,
        description="整体市场情绪判断"
    )

    key_topics: List[str] = Field(
        ...,
        description="主要讨论主题（3-5条）"
    )

    risk_flags: List[str] = Field(
        ...,
        description="主要风险信号（2-5条）"
    )


# ============================================================
# 2. Node 构造函数
# ============================================================

from langchain_core.prompts import ChatPromptTemplate


def create_cluster_sentiment_analyst(llm):

    def cluster_sentiment_node(state: dict):

        # ===== 1. 聚类舆情数据 =====
        clusters = (
            state.get("analysis", {})
                .get("cluster_summary", {})
                .get("cluster_summaries", [])
        )

        # ===== 2. 行情语义检索数据 =====
        retrieval = (
            state.get("analysis", {})
                .get("semantic_retrieval", {})
        )

        query = retrieval.get("query", "")
        top_docs = retrieval.get("results", [])

        # 如果两类输入都没有
        if not clusters and not top_docs:
            return {
                "analysis": {
                    "sentiment_summary": {
                        "overview": "暂无舆情数据可分析。",
                        "sentiment": "neutral",
                        "key_topics": [],
                        "risk_flags": []
                    }
                }
            }

        # ===== 3. 聚类输入文本 =====
        cluster_text = ""
        if clusters:
            for c in clusters:
                quotes = "\n- ".join(
                    c.get("representative_quotes", [])
                )

                cluster_text += f"""
类别 {c['cluster_id']}（规模 {c['size']}）
主题: {c['topic']}
摘要: {c['summary']}
关键词: {', '.join(c['keywords'])}
代表性言论:
- {quotes}

"""

        # ===== 4. 行情检索输入文本 =====
        retrieval_text = ""
        if top_docs:
            retrieval_text += f"""
【行情语义检索证据】
检索 Query: {query}

Top 相关讨论：
"""
            for r in top_docs:
                retrieval_text += (
                    f"- (score={r['score']:.2f}) "
                    f"{r['content']} "
                    f"(评论数={r['comment_count']})\n"
                )
        else:
            retrieval_text = "\n【行情语义检索证据】暂无。\n"

        # ===== 5. Prompt =====
        system_message = """
你是金融舆情分析助手。

任务：
- 基于“股吧聚类讨论” + “行情语义检索证据”，总结行业整体市场情绪。

分析要求：
1. 聚类部分代表长期讨论结构。
2. 检索部分代表当前行情最相关的敏感舆论。
3. 必须综合两部分证据，不允许编造。

输出必须符合 schema：
- overview: 200字以内
- sentiment: bullish / bearish / neutral
- key_topics: 3~6个核心话题
- risk_flags: 0~5条潜在风险提示
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                (
                    "human",
                    "【聚类舆情】\n{cluster_text}\n\n"
                    "{retrieval_text}"
                )
            ]
        )

        # ===== 6. Structured Output =====
        structured_llm = llm.with_structured_output(
            ClusterSentimentAnalysis
        )

        chain = prompt | structured_llm

        # ===== 7. 调用模型 =====
        result: ClusterSentimentAnalysis = chain.invoke(
            {
                "cluster_text": cluster_text,
                "retrieval_text": retrieval_text
            }
        )

        # ===== 8. Patch 写回 =====
        return {
            "analysis": {
                "sentiment_summary": result.model_dump()
            }
        }

    return cluster_sentiment_node

