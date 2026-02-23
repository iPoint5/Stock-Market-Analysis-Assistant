import json
import requests
from lxml import etree
from datetime import datetime


def fetch_sina_roll_news(page=1, save_path=None):
    """
    抓取新浪财经滚动新闻，并返回 enrich_news 可直接处理的 dict 结构

    输出格式：
    {
        "fetched_at": "...",
        "source": "sina",
        "page": 1,
        "news": [ ... ]
    }
    """

    url = f"https://finance.sina.com.cn/roll/c/56592.shtml?page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    resp = requests.get(url, headers=headers, timeout=10)
    resp.encoding = "utf-8"

    html = etree.HTML(resp.text)
    items = html.xpath('//ul[@id="listcontent"]/li')

    news_list = []

    for idx, li in enumerate(items):
        try:
            title = li.xpath('.//a/text()')[0].strip()
            link = li.xpath('.//a/@href')[0].strip()
            publish_time = li.xpath('.//span/text()')[0].strip()

            news_list.append({
                "id": idx,
                "title": title,
                "url": link,
                "publish_time": publish_time,
                "source": "sina",

                # enrich_news 会补全这些字段
                "industry": None,
                "stock_code": [],
                "stock": []
            })

        except IndexError:
            continue

    # 关键：包装成 enrich_news 标准输入结构
    result = {
        "fetched_at": datetime.now().isoformat(),
        "source": "sina",
        "page": page,
        "news": news_list
    }

    # 可选：保存 JSON
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result
