def build_initial_state(
    trade_date: str,
    industry: str,
    time_window: str = "1d"
):
    """
    行业舆情分析任务的最小初始化 State

    原则：
    - 初始化只建立结构，不填充新闻/舆情数据
    - 后续由专门函数逐步写入
    """

    state = {
        # 任务元信息（初始化时唯一确定）
        "meta": {
            "trade_date": trade_date,
            "industry": industry,
            "time_window": time_window,
        },
        # 新闻事件
        "news_events": {
            "raw_count": 0,
            "events": []
        },
        # 舆情聚类
        "sentiment_clusters": {
            "best_k": None,
            "best_score": None,
            "clusters": []
        },
        # 分析输出
        "analysis": {
            "industry_news_summary": None,
            "sentiment_summary": None,
            "final_report": None,
        }
    }
    return state

def fill_news_events(state: dict, news_events: list):
    """
    将新闻事件写入 state
    """
    state["news_events"]["raw_count"] = len(news_events)
    state["news_events"]["events"] = news_events
    return state
# 这个函数已经符合要求了
def fill_sentiment_clusters(state, cluster_result):

    state["sentiment_clusters"]["best_k"] = cluster_result.get("best_k")
    state["sentiment_clusters"]["best_score"] = cluster_result.get("best_score")
    state["sentiment_clusters"]["clusters"] = cluster_result.get("cluster_summaries", [])

    return state



def fill_semantic_retrieval_results(state, query, results, top_k=5):

    state["analysis"]["semantic_retrieval"] = {
        "query": query,
        "top_k": top_k,
        "results": results['results'][:top_k]
    }

    return state

