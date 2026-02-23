
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

def main():

    # ===== Step0: 初始化 LLM =====
    llm = ChatOllama(
        model="qwen2.5:7b",
        temperature=0
    )
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

    # ===== Step3: 抓取新闻 =====
    stock_mapping = load_stock_mapping(csv_path)
    raw_news = fetch_sina_roll_news(page=1)

    enriched_news = enrich_news(stock_mapping, raw_news)

    filtered_news = filter_news_by_industry(
        enriched_news["news"],
        [industry]
    )
  
    compressed_news = compress_news(filtered_news)
    news_source = "新浪财经"

    # 写入 state
    state = fill_news_events(state, compressed_news)

    # ===== Step4: 新闻分析 Node =====
    news_node = create_structured_news_analyst(llm)
    news_patch = news_node(state)

    state["analysis"].update(news_patch["analysis"])
    state["meta"].update(news_patch["meta"])

    # ===== Step5: 股吧聚类 =====
    posts=load_guba_texts(
        f"https://guba.eastmoney.com/list,002165.html"
    )
    # 做个语义检索
    mode, _ = select_query_mode()
    relevance = guba_semantic_search(documents=posts, query=QUERY_DICT[mode])
    
    state = fill_semantic_retrieval_results(state, QUERY_DICT[mode], relevance, top_k=5)

    text = [p["text"] for p in posts if p["text"].strip()]
    cluster_result = run_guba_sentiment_clustering(
        text
    )

    # 写入原始聚类
    state = fill_sentiment_clusters(state, cluster_result)
    # ===== Step6: 聚类总结 =====
    summarizer_agent = ClusterSummarizerAgent(llm)
    cluster_summary = summarizer_agent.run(cluster_result)
    print(cluster_summary)
    state["analysis"]["cluster_summary"] = cluster_summary
    # ===== Step7: 舆情分析 Node =====
    sentiment_node = create_cluster_sentiment_analyst(llm)
    sent_patch = sentiment_node(state)

    state["analysis"].update(sent_patch["analysis"])

    # ===== Step8: 保存 state =====
    with open("state.json", "w", encoding="utf-8-sig") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

    print("Done. state.json saved.")
    



if __name__ == "__main__":
    main()
