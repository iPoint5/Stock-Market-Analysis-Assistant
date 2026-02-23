import json
import csv
from collections import defaultdict
from .sina_news_crawler import fetch_sina_roll_news
# =========================
# 1. 读取股票-行业 CSV
# =========================
def load_stock_mapping(csv_path):
    """
    返回：
    company_name -> {
        'industry_name': str,
        'stock_code': str
    }
    """
    mapping = {}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["company_name"]] = {
                "industry_name": row["industry_name"],
                "stock_code": row["stock_code"]
            }

    return mapping

# 2. 新闻匹配逻辑
def enrich_news(stock_mapping, news_data):

    for item in news_data["news"]:
        title = item["title"]

        industries = set()
        stocks = []
        stock_codes = []

        for company, info in stock_mapping.items():
            full_code = info["stock_code"]

            # 去掉 .SZ / .SH 后缀，只保留数字部分
            pure_code = full_code.split(".")[0]

            if (company in title) or (pure_code in title):
                stocks.append(company)
                stock_codes.append(full_code)
                industries.add(info["industry_name"])

        item["industry"] = list(industries) if industries else None
        item["stock"] = stocks
        item["stock_code"] = stock_codes

    return news_data



# =========================
# 3. 行业筛选
# =========================
def filter_news_by_industry(news_list, target_industries):
    """
    纯数据函数：筛选指定行业新闻
    """

    if isinstance(target_industries, str):
        target_industries = {target_industries}
    else:
        target_industries = set(target_industries)

    result = []

    for news in news_list:
        industries = news.get("industry")
        if not industries:
            continue

        if set(industries) & target_industries:
            result.append(news)

    return result


# =========================
# 4. 新闻压缩（事件级）
# =========================
def compress_news(news_list):
    """
    将新闻压缩成事件级输入，减少 token + 去重
    """

    events = defaultdict(lambda: {"count": 0, "headlines": []})

    for n in news_list:
        if not n.get("stock"):
            continue

        company = n["stock"][0]
        title = n["title"]

        # 简单事件 key（公司 + 标题前12字）
        key = (company, title[:12])

        events[key]["count"] += 1
        events[key]["headlines"].append(title)

    compressed = []
    for (company, _), info in events.items():
        compressed.append({
            "company": company,
            "headline": info["headlines"][0],
            "duplicates": info["count"]
        })

    return compressed


# =========================
# 5. 主入口
# =========================
if __name__ == "__main__":

    # 1）加载映射表
    stock_mapping = load_stock_mapping(
        r"E:\code\ai agnet开发\a股助手\searching_agent\dataflows\industry_stock_mapping.csv"
    )

    # 2）抓取新闻（直接返回 dict）
    data = fetch_sina_roll_news(page=1)

    # 3）补全行业股票信息
    data = enrich_news(stock_mapping, data)

    # 4）筛选行业
    filtered_news = filter_news_by_industry(
        data["news"],
        ["化工"]
    )

    # 5）压缩事件
    compressed = compress_news(filtered_news)

    print(compressed)
