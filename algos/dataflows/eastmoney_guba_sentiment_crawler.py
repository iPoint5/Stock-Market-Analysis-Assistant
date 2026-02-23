import re
import json
import requests


def fetch_guba_article_list(url, timeout=10):
    """
    从东方财富股吧页面中提取 article_list.re 舆情帖子列表
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
    }

    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    html = resp.text

    # 精确匹配 var article_list = {...};
    pattern = re.compile(
        r"var\s+article_list\s*=\s*(\{.*?\})\s*;",
        re.S
    )

    match = pattern.search(html)
    if not match:
        raise ValueError("article_list not found in page")

    raw_json = match.group(1)

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError("article_list JSON parse failed") from e

    return data.get("re", [])


def is_title_only_post(p):
    """
    判断是否为「标题即全部语义」的舆情帖子
    """
    if not p.get("post_title"):
        return False

    if p.get("post_content"):
        return False

    if p.get("reply_list"):
        return False

    if p.get("post_type") in (1, 3):
        return False

    return True


def normalize_posts(posts):
    """
    仅保留「标题级舆情帖子」
    用于大众情绪分析 / 语义聚类 / Agent 推理
    """
    result = []

    total = len(posts)
    kept = 0

    for p in posts:
        if not is_title_only_post(p):
            continue

        core = {
            "post_id": p.get("post_id"),
            "asset_code": p.get("stockbar_code"),
            "asset_name": p.get("stockbar_name"),
            "text": p.get("post_title", ""),
            "publish_time": p.get("post_publish_time"),
            "last_active_time": p.get("post_last_time"),
            "author_id": p.get("user_id"),
            "metrics": {
                "click": p.get("post_click_count", 0),
                "comment": p.get("post_comment_count", 0),
                "forward": p.get("post_forward_count", 0),
                "has_pic": p.get("post_has_pic", False),
            },
            "post_type": p.get("post_type", 0),
        }

        result.append(core)
        kept += 1

    # ✅简洁打印
    print(f"[normalize_posts] 输入 {total} 条帖子 → 保留 {kept} 条标题帖")

    return result


# ===================== 主函数 =====================
def load_guba_texts(url):
    raw_posts = fetch_guba_article_list(url)
    posts = normalize_posts(raw_posts)

    return posts
