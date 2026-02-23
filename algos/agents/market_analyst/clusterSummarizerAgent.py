from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# Schema：LLM 输出结构
# ============================================================

class ClusterLLMSummary(BaseModel):
    topic: str = Field(..., description="6~12字主题概括")
    summary: str = Field(..., description="1~2句讨论焦点总结")
    keywords: List[str] = Field(..., description="3~6个关键词")


# ============================================================
# Agent：Cluster Summarizer
# ============================================================

class ClusterSummarizerAgent:
    """
    Cluster Summarizer Agent（结构化版本）

    输入: cluster_result["clusters"]
    输出: cluster_summaries（稳定字段）
    """

    def __init__(self, llm, top_k_quotes=2):
        self.llm = llm
        self.top_k_quotes = top_k_quotes

    # -----------------------------
    # Step 1: evidence quotes（严格原文）
    # -----------------------------
    def extract_quotes(self, texts):
        return texts[: self.top_k_quotes]

    # -----------------------------
    # Step 2: LLM 总结（结构化输出）
    # -----------------------------
    def llm_summarize(self, cluster_id, size, texts):

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
你是金融舆情聚类总结智能体。

任务：
- 总结该聚类讨论主题

要求：
- topic：6~12字
- summary：1~2句
- keywords：3~6个
- 禁止编造输入中不存在的信息
- 输出必须严格符合结构化 schema
"""
                ),
                (
                    "human",
                    """
cluster_id = {cluster_id}
评论数量 = {size}

代表性评论如下：
{texts}
"""
                )
            ]
        )
        # 结构化输出
        structured_llm = self.llm.with_structured_output(
            ClusterLLMSummary
        )
        chain = prompt | structured_llm
        result: ClusterLLMSummary = chain.invoke(
            {
                "cluster_id": cluster_id,
                "size": size,
                "texts": "\n".join(texts)
            }
        )

        return result
    # -----------------------------
    # Step 3: 主入口
    # -----------------------------
    def run(self, cluster_result):

        output = {
            "best_k": cluster_result.get("best_k"),
            "best_score": cluster_result.get("best_score"),
            "cluster_summaries": []
        }

        for cluster in cluster_result["clusters"]:

            cid = cluster["cluster_id"]
            size = cluster["size"]
            texts = cluster["representative_texts"]

            # evidence quotes（原文）
            quotes = self.extract_quotes(texts)

            # LLM 总结（结构化）
            llm_result = self.llm_summarize(cid, size, texts)

            output["cluster_summaries"].append({
                "cluster_id": cid,
                "size": size,
                "topic": llm_result.topic,
                "summary": llm_result.summary,
                "keywords": llm_result.keywords,
                "representative_quotes": quotes
            })

        return output
