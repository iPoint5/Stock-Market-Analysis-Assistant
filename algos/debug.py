
import json
import pandas as pd
from pathlib import Path
from langchain_ollama import ChatOllama

from dataflows.news_selector import (
    load_stock_mapping,
    enrich_news,
    filter_news_by_industry,
    compress_news
)
from dataflows.sina_news_crawler import fetch_sina_roll_news
from dataflows.sentiment_clustering import run_guba_sentiment_clustering
from dataflows.eastmoney_guba_sentiment_crawler import load_guba_texts
from agents.market_analyst.state import (
    build_initial_state,
    fill_news_events,
    fill_sentiment_clusters,
    fill_semantic_retrieval_results
)
from dataflows.semantic_relevance import guba_semantic_search,QUERY_DICT,select_query_mode
from agents.market_analyst.market_analyst import create_structured_news_analyst
from agents.market_analyst.sentiment_analyst import create_cluster_sentiment_analyst
from agents.market_analyst.clusterSummarizerAgent import ClusterSummarizerAgent
from sentence_transformers import SentenceTransformer
def main():

    # # ===== Step0: 初始化 LLM =====
    # llm = ChatOllama(
    #     model="qwen2.5:7b",
    #     temperature=0
    # )
    # print(type(llm))
    # print(llm)

    stock = "红宝丽"
   
    # ===== Step1: 获取行业 =====
    BASE_DIR = Path(__file__).resolve().parent
    csv_path = BASE_DIR / "dataflows" / "industry_stock_mapping.csv"

    industry_df = pd.read_csv(csv_path)
    industry = industry_df[industry_df["company_name"] == stock]["industry_name"].values[0]

    # ===== Step2: 初始化 state =====
    state = build_initial_state(
        trade_date="2026-02-05",
        industry=industry
    )

    posts=load_guba_texts(
        f"https://guba.eastmoney.com/list,002165.html"
    )
    print(posts)


if __name__ == "__main__":
    main()