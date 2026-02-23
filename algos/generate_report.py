import json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def generate_full_analysis_pdf(
    json_path="state.json",
    output_pdf="analysis_report2.pdf"
):
    # ===== 1. 注册中文字体 =====
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    # ===== 2. 读取 state.json =====
    with open(json_path, "r", encoding="utf-8-sig") as f:
        state = json.load(f)


    meta = state.get("meta", {})
    analysis = state.get("analysis", {})

    # ===== 3. PDF 文档初始化 =====
    doc = SimpleDocTemplate(output_pdf, pagesize=A4)
    story = []

    # ===== 4. 样式定义 =====
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleChinese",
        parent=styles["Title"],
        fontName="STSong-Light",
        fontSize=20,
        leading=28,
        alignment=1,
        spaceAfter=20
    )

    ch_style = ParagraphStyle(
        "Chinese",
        parent=styles["Normal"],
        fontName="STSong-Light",
        fontSize=12,
        leading=18,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "SubtitleChinese",
        parent=styles["Heading2"],
        fontName="STSong-Light",
        fontSize=15,
        leading=22,
        spaceBefore=14,
        spaceAfter=10
    )

    cluster_title_style = ParagraphStyle(
        "ClusterTitle",
        parent=styles["Heading3"],
        fontName="STSong-Light",
        fontSize=13,
        leading=20,
        spaceBefore=10,
        spaceAfter=6
    )

    # ===== 5. 标题 =====
    story.append(Paragraph("行业舆情分析报告", title_style))

    # ===== 6. Meta 信息 =====
    story.append(Paragraph("基础信息", subtitle_style))
    story.append(Paragraph(f"交易日期：{meta.get('trade_date')}", ch_style))
    story.append(Paragraph(f"行业：{meta.get('industry')}", ch_style))
    story.append(Paragraph(f"时间窗口：{meta.get('time_window')}", ch_style))
    story.append(Spacer(1, 12))

    # ===== 7. 新闻分析 industry_news_summary =====
    industry_news_summary = analysis.get("industry_news_summary")
    if industry_news_summary:
        story.append(Paragraph("新闻事件总结", subtitle_style))

        # 新闻要点（industry_news_summary 是一个列表）
        story.append(Paragraph("新闻要点：", ch_style))
        for item in industry_news_summary:
            story.append(Paragraph("• " + item, ch_style))
        story.append(Spacer(1, 10))

        # 行业影响
        industry_implications = analysis.get("industry_implications", [])
        if industry_implications:
            story.append(Paragraph("行业影响：", ch_style))
            for item in industry_implications:
                story.append(Paragraph("• " + item, ch_style))
            story.append(Spacer(1, 10))

        # ===== 公司影响（紧凑版：每公司一段）=====
        company_implications = analysis.get("company_implications", [])
        if company_implications:
            story.append(Paragraph("公司影响：", ch_style))

            for comp in company_implications:
                company = comp.get("company", "")
                impacts = comp.get("impacts", [])

                if impacts:
                    impacts_text = "；".join(impacts)
                else:
                    impacts_text = "暂无明确影响"

                # 每家公司一段：公司名加粗 + impacts 连在后面
                story.append(
                    Paragraph(
                        f"<b>{company}</b>：{impacts_text}",
                        ch_style
                    )
                )

            # 公司之间整体留一点空白
            story.append(Spacer(1, 8))

        # 市场情绪与结论
        market_sentiment = analysis.get("market_sentiment")
        if market_sentiment:
            story.append(
                Paragraph(
                    f"市场情绪：{market_sentiment}",
                    ch_style
                )
            )

        conclusion = analysis.get("conclusion")
        if conclusion:
            story.append(
                Paragraph(
                    f"新闻结论：{conclusion}",
                    ch_style
                )
            )
        story.append(Spacer(1, 15))

    # ===== 8. 舆情总结 sentiment_summary =====
    sentiment_summary = analysis.get("sentiment_summary")
    if sentiment_summary:
        story.append(Paragraph("舆情概览", subtitle_style))

        # 舆情概述
        overview = sentiment_summary.get("overview")
        if overview:
            story.append(Paragraph("概述：", ch_style))
            story.append(Paragraph(overview.replace("\n", "<br/>"), ch_style))
            story.append(Spacer(1, 8))

        # 情绪倾向
        sentiment = sentiment_summary.get("sentiment")
        if sentiment:
            sentiment_map = {
                "bullish": "看涨",
                "bearish": "看跌",
                "neutral": "中性"
            }
            story.append(
                Paragraph(
                    f"情绪倾向：{sentiment_map.get(sentiment, sentiment)}",
                    ch_style
                )
            )
            story.append(Spacer(1, 8))

        # 关键话题
        key_topics = sentiment_summary.get("key_topics", [])
        if key_topics:
            story.append(Paragraph("关键话题：", ch_style))
            story.append(Paragraph("、".join(key_topics), ch_style))
            story.append(Spacer(1, 8))

        # 风险提示
        risk_flags = sentiment_summary.get("risk_flags", [])
        if risk_flags:
            story.append(Paragraph("风险提示：", ch_style))
            for risk in risk_flags:
                story.append(Paragraph("• " + risk, ch_style))

        story.append(Spacer(1, 15))

    # ===== 9. 语义检索结果 semantic_retrieval =====
    semantic_retrieval = analysis.get("semantic_retrieval")
    if semantic_retrieval:
        story.append(Paragraph("语义检索结果", subtitle_style))
        story.append(Paragraph(f"查询语句：{semantic_retrieval.get('query')}", ch_style))
        story.append(Paragraph(f"返回数量：{semantic_retrieval.get('top_k')}", ch_style))
        story.append(Spacer(1, 8))

        story.append(Paragraph("检索结果：", ch_style))
        results = semantic_retrieval.get("results", [])
        for i, result in enumerate(results, 1):
            score = result.get("score", 0)
            content = result.get("content", "")
            comment_count = result.get("comment_count", 0)
            story.append(
                Paragraph(
                    f"{i}. [分数: {score:.4f}] [评论数: {comment_count}] {content}",
                    ch_style
                )
            )
        story.append(Spacer(1, 15))

    # ===== 10. 聚类总结 cluster_summary =====
    cluster_summary = analysis.get("cluster_summary")
    if cluster_summary:
        story.append(Paragraph("股吧聚类分析", subtitle_style))
        story.append(
            Paragraph(
                f"最佳聚类数 K = {cluster_summary.get('best_k')}，"
                f"得分 = {cluster_summary.get('best_score'):.3f}",
                ch_style
            )
        )
        story.append(Spacer(1, 10))

        for cluster in cluster_summary.get("cluster_summaries", []):
            story.append(
                Paragraph(
                    f"聚类 {cluster['cluster_id']}（规模：{cluster['size']}）",
                    cluster_title_style
                )
            )
            story.append(Paragraph(f"主题：{cluster['topic']}", ch_style))
            story.append(Paragraph(f"摘要：{cluster['summary']}", ch_style))

            story.append(
                Paragraph(
                    "关键词：" + "、".join(cluster["keywords"]),
                    ch_style
                )
            )

            story.append(Paragraph("代表性言论：", ch_style))
            for quote in cluster.get("representative_quotes", []):
                story.append(Paragraph("• " + quote, ch_style))

            story.append(Spacer(1, 12))

    # ===== 11. final_report =====
    final_report = analysis.get("final_report")
    if final_report:
        story.append(Paragraph("最终综合报告", subtitle_style))
        story.append(Paragraph(final_report.replace("\n", "<br/>"), ch_style))
        story.append(Spacer(1, 12))

    # ===== 12. 输出 PDF =====
    doc.build(story)
    print("PDF 已生成：", output_pdf)


if __name__ == "__main__":
    generate_full_analysis_pdf(
        json_path="state.json",
        output_pdf="analysis_report.pdf"
    )
