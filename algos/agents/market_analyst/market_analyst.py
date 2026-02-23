import json
from typing import List, Literal

from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# 1. 定义结构化输出 Schema（Pydantic）
# ============================================================

class CompanyImpact(BaseModel):
    """
    单个公司影响对象
    """
    company: str = Field(..., description="Company name")
    impacts: List[str] = Field(..., description="List of short impact statements")


class NewsAnalysis(BaseModel):
    """
    新闻分析结构化输出
    """
    news_summary: List[str] = Field(
        ..., description="Key news event summary bullets"
    )

    industry_implications: List[str] = Field(
        ..., description="Industry-level implications"
    )

    company_implications: List[CompanyImpact] = Field(
        ..., description="Company-level impacts"
    )

    market_sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        ..., description="Overall market sentiment"
    )

    conclusion: str = Field(
        ..., description="Short conclusion sentence"
    )


# ============================================================
# 2. 创建 Structured News Analyst Node
# ============================================================

def create_structured_news_analyst(llm):
    """
    返回一个 news_analyst_node(state) 节点函数
    - 输入：state（包含 meta + news_events）
    - 输出：patch（写回 analysis 字段）
    """

    def news_analyst_node(state):

        # =====================================================
        # A. Meta 信息
        # =====================================================
        meta = state.get("meta", {})
        trade_date = meta.get("trade_date", "unknown")
        industry = meta.get("industry", "unknown")
        time_window = meta.get("time_window", "unknown")

        # =====================================================
        # B. 新闻事件输入
        # =====================================================
        events = state.get("news_events", {}).get("events", [])

        if not events:
            return {
                "analysis": {
                    "industry_news_summary": ["No significant news events found."],
                    "industry_implications": [],
                    "company_implications": [],
                    "market_sentiment": "neutral",
                    "conclusion": "No major industry news impact detected."
                }
            }

        # 控制输入长度（防止 token 爆炸）
        events = events[:20]

        # 转成 JSON 输入模型
        news_text = json.dumps(events, ensure_ascii=False, indent=2)

        # =====================================================
        # C. Prompt 设计
        # =====================================================
        system_message = f"""
You are a professional financial news analyst.

You are given structured industry news events.

You MUST analyze ALL provided events.

Return ONLY a JSON object that matches the required schema.

Context:
Date: {trade_date}
Industry: {industry}
Time window: {time_window}
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                ("human", "Here are the news events (JSON):\n{news_data}")
            ]
        )

        # =====================================================
        # D. 核心修复：使用 LangChain Structured Output
        # =====================================================
        structured_llm = llm.with_structured_output(NewsAnalysis)

        chain = prompt | structured_llm

        # =====================================================
        # E. 调用模型（不会返回字符串，而是结构化对象）
        # =====================================================
        result: NewsAnalysis = chain.invoke(
            {"news_data": news_text}
        )

        # =====================================================
        # F. Patch 写回逻辑修复（拆分字段，而不是塞一个大对象）
        # =====================================================
        patch = {
            "analysis": {
                # 修复点：summary 字段只存 summary 列表
                "industry_news_summary": result.news_summary,

                # 其他字段单独写回
                "industry_implications": result.industry_implications,
                "company_implications": [
                    ci.model_dump() for ci in result.company_implications
                ],
                "market_sentiment": result.market_sentiment,
                "conclusion": result.conclusion,
            },

            "meta": {
                **meta,
                "used_news_count": len(events)
            }
        }

        return patch

    return news_analyst_node
