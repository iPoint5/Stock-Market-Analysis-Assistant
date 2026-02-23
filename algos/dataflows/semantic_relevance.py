from sentence_transformers import SentenceTransformer
import numpy as np

QUERY_DICT = {
    "extreme_bullish": "明天涨停 一字板 起飞 主升浪开启 牛市来了 满仓梭哈 妖股连板 必翻倍",

    "extreme_bearish": "崩盘 跳水 大跌 跌停 主力出货 跑路 清仓割肉 完蛋了 退市风险 暴雷利空",

    "strong_divergence": "多空大战 分歧巨大 吵翻了 骂战 情绪爆炸 看多看空两极化 博弈激烈",

    "main_force_behavior": "主力洗盘 主力吸筹 主力出货 游资来了 机构进场 尾盘拉升 大单砸盘 控盘明显",

    "short_term_forecast": "明天怎么走 明天还能涨吗 明天会跌吗 高开低开 还能上车吗 下周走势预测",

    "risk_events": "证监会立案 投资者索赔 财务造假 重大利空 监管处罚 暴雷预警 退市警报"
}

def select_query_mode():
    """
    终端输入查询模式，返回对应查询语句
    """
    print("\n====== 舆情查询模式选择 ======\n")

    keys = list(QUERY_DICT.keys())

    for i, k in enumerate(keys, start=1):
        print(f"{i}. {k}")

    print("\n输入模式编号或模式名称：")

    user_input = input(">>> ").strip()

    # 允许输入编号
    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(keys):
            mode = keys[idx]
            return mode, QUERY_DICT[mode]

    # 允许输入key名称
    if user_input in QUERY_DICT:
        return user_input, QUERY_DICT[user_input]

    print("\n输入无效，请重新运行选择\n")
    return None, None

import os
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from huggingface_hub import snapshot_download


def guba_semantic_search(
    query: str,
    documents: list,
    model_repo: str = "valuesimplex-ai-lab/fin-retriever-base",
    top_k: int = 10,
    model_root: str = "./models"
):
    """
    东方财富股吧语义检索函数（工程稳定版）

    特性：
    - 优先本地加载模型
    - 本地缺失自动下载
    - cosine similarity 标准化
    - TopK 使用 torch.topk（避免 numpy/tensor 混用错误）
    - 返回统一 retrieval pack
    """

    # ===== 1. Query Prompt =====
    optimized_query = "为这个句子生成表示以用于检索相关文章：" + query

    # ===== 2. 本地模型路径 =====
    local_model_path = os.path.join(
        model_root,
        "valuesimplex-ai-lab",
        "fin-retriever-base"
    )

    # ===== 3. 自动下载（若不存在） =====
    if not os.path.exists(local_model_path):
        print("[Model] 本地模型不存在，开始下载...")
        snapshot_download(
            repo_id=model_repo,
            local_dir=local_model_path,
            local_dir_use_symlinks=False
        )
        print("[Model] 下载完成")

    # ===== 4. 加载模型（只加载本地目录） =====
    print("[Model] Loading from:", local_model_path)
    model = SentenceTransformer(local_model_path)

    # ===== 5. 文档格式化 =====
    formatted_docs = []
    for doc in documents:
        formatted_docs.append(
            f"文章标题：{doc['text']}\n"
            f"股吧名称：{doc['asset_name']}\n"
            f"评论数量：{doc['metrics']['comment']}\n"
        )

    print(f"[Search] 文档数={len(formatted_docs)}")

    # ===== 6. 向量编码（归一化） =====
    all_texts = [optimized_query] + formatted_docs
    embeddings = model.encode(
        all_texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    query_vector = embeddings[0]
    doc_vectors = embeddings[1:]

    # ===== 7. Cosine Similarity（torch tensor）=====
    scores = cos_sim(query_vector, doc_vectors)[0]  # shape = (N,)

    # ===== 8. TopK（关键修复：不要用 np.argsort）=====
    k = min(top_k, len(scores))

    top_scores, top_indices = torch.topk(scores, k=k)

    # 转成 python list
    top_scores = top_scores.tolist()
    top_indices = top_indices.tolist()

    # ===== 9. 构造结果 =====
    results = []
    for score, idx in zip(top_scores, top_indices):
        doc = documents[idx]
        results.append({
            "score": float(score),
            "content": doc["text"],
            "comment_count": doc["metrics"]["comment"],
        })

    # ===== 10. 返回 Retrieval Pack =====
    return {
        "query": query,
        "top_k": top_k,
        "results": results
    }





# ================== 使用示例 ==================
if __name__ == "__main__":
    url = "https://guba.eastmoney.com/list,002165.html"
    query = "红宝丽市场行情分析 / 走势判断 / 预期描述"

    results = guba_semantic_search(query, url, top_k=5)

    print("【查询】:", query)
    print("【Top匹配结果】")
    for r in results:
        print(f"分数: {r['score']:.4f} | 标题: {r['title']} | 评论数: {r['comment_count']}")
