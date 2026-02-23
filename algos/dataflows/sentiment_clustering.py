import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score

from .eastmoney_guba_sentiment_crawler import (
    load_guba_texts
)


#  记得调用load_guba_texts函数加载文本


def build_tfidf_lsa_matrix(texts):
    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 4),
        max_df=0.9,
        min_df=2,
        max_features=3000
    )

    tfidf_matrix = vectorizer.fit_transform(texts)

    lsa = TruncatedSVD(n_components=2, random_state=42)
    lsa_matrix = lsa.fit_transform(tfidf_matrix)

    return lsa_matrix

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_distances


def cluster_and_pack_for_agent(
    texts,
    lsa_matrix,
    k_min=2,
    k_max=8,
    top_n_sentences=5
):
    """
    输出标准聚类结构，供 LLM 智能体使用
    """

    if len(texts) < 5:
        return {
            "best_k": 1,
            "best_score": 0.0,
            "clusters": [
                {
                    "cluster_id": 0,
                    "size": len(texts),
                    "representative_texts": texts[:top_n_sentences]
                }
            ]
        }

    best_score = -1
    best_k = None
    best_labels = None
    best_model = None

    # ===== 1. 遍历 k，选择最优 silhouette =====
    for k in range(k_min, min(k_max, len(texts) - 1) + 1):

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(lsa_matrix)

        if len(set(labels)) < 2:
            continue

        score = silhouette_score(lsa_matrix, labels)

        if score > best_score:
            best_score = score
            best_k = k
            best_labels = labels
            best_model = kmeans

    # 如果 silhouette 失败
    if best_k is None:
        best_k = 1
        best_labels = np.zeros(len(texts), dtype=int)

    # ===== 2. 打包 clusters =====
    clusters = []

    for cluster_id in range(best_k):
        idxs = np.where(best_labels == cluster_id)[0]

        cluster_texts = [texts[i] for i in idxs]
        cluster_vectors = lsa_matrix[idxs]

        # 单簇情况直接取前 top_n
        if best_model is None:
            representative_texts = cluster_texts[:top_n_sentences]
        else:
            center = best_model.cluster_centers_[cluster_id].reshape(1, -1)

            distances = cosine_distances(cluster_vectors, center).flatten()
            sorted_idx = np.argsort(distances)

            representative_texts = [
                cluster_texts[i] for i in sorted_idx[:top_n_sentences]
            ]

        clusters.append({
            "cluster_id": int(cluster_id),
            "size": int(len(idxs)),
            "representative_texts": representative_texts
        })

    return {
        "best_k": int(best_k),
        "best_score": float(best_score),
        "clusters": clusters
    }
def run_guba_sentiment_clustering(texts):
    """
    一键完成：
    东方财富股吧抓取 → 文本清洗 → TF-IDF → LSA → 聚类 → 打包输出
    """

    print("向量化 + 降维...")
    lsa_matrix = build_tfidf_lsa_matrix(texts)

    print("聚类并打包...")
    cluster_result = cluster_and_pack_for_agent(
        texts=texts,
        lsa_matrix=lsa_matrix,
        k_min=2,
        k_max=8,
        top_n_sentences=5
    )

    return cluster_result




