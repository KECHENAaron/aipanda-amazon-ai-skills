# AIPANDA public curation, modified 2026-11-14; AGPL-3.0; see PUBLIC_CHANGES.md.
"""Run the independent analyzer with explicit grain and observable provenance."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

import pandas as pd
import analyze_search_term_decisions as engine
from clean_search_term_report import build_normalized_frame


def load_config(path):
    values = json.loads(Path(path).read_text()) if path else {}
    if not isinstance(values, dict) or set(values) - {"thresholds", "protected_keywords", "goal", "competitor_brands"}:
        raise ValueError("配置只支持 thresholds / protected_keywords / goal / competitor_brands")
    thresholds = dict(engine.DEFAULT_THRESHOLDS)
    for key, value in values.get("thresholds", {}).items():
        if key not in thresholds or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"无效阈值 {key}")
        if any(k in key for k in ["band", "similarity"]) and value > 1:
            raise ValueError(f"比例阈值 {key} 必须在 0–1")
        thresholds[key] = value
    protected = values.get("protected_keywords", [])
    if not isinstance(protected, list) or any(not isinstance(x, str) or not x.strip() for x in protected):
        raise ValueError("protected_keywords 必须为非空字符串数组，可为空数组")
    if values.get("goal", "diagnostic") not in {"diagnostic", "profit", "launch", "volume", "clearance", "relaunch"}:
        raise ValueError("未知 goal")
    brands=values.get('competitor_brands',[])
    if not isinstance(brands,list) or any(not isinstance(x,str) or not x.strip() for x in brands):raise ValueError('competitor_brands 必须为字符串列表')
    return thresholds, protected, values.get("goal", "diagnostic"), brands


def period_for(path, start, end):
    if bool(start) != bool(end):
        raise ValueError("start-date 和 end-date 必须同时提供")
    if not start:
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", Path(path).stem)
        if len(dates) >= 2:
            start, end = dates[-2:]
    if not start:
        raise ValueError("汇总数据需要明确起止日期；不可伪造逐日数据")
    lo, hi = pd.Timestamp(start), pd.Timestamp(end)
    if lo > hi:
        raise ValueError("开始日期晚于结束日期")
    return lo, hi


def source_entities(frame):
    aliases = {"campaign_id": ["Campaign ID", "campaign_id"], "ad_group_id": ["Ad Group ID", "ad_group_id"], "record_id": ["Source Record ID", "record_id"], "campaign_name": ["campaign_name"], "ad_group_name": ["ad_group_name"], "match_type": ["match_type"]}
    result = {}
    for term, group in frame.groupby("search_term"):
        items = []
        for _, row in group.iterrows():
            item = {key: str(row[col]) for key, options in aliases.items() for col in options[:1] if col in row.index and pd.notna(row[col])}
            for key, options in aliases.items():
                if key not in item:
                    for col in options:
                        if col in row.index and pd.notna(row[col]):
                            item[key] = str(row[col]); break
            if item not in items:
                items.append(item)
        result[term] = json.dumps(items, ensure_ascii=False)
    return result


def analyze(args):
    path = Path(args.input_file).expanduser().resolve()
    df, metadata = build_normalized_frame(path, brand=args.brand)
    if metadata["missing_core_fields"]:
        raise ValueError("缺少核心字段：" + ",".join(metadata["missing_core_fields"]))
    asin = engine.select_asin(df, metadata, args.asin)
    excluded_asin = int((df["asin"] != asin).sum())
    df = df[df["asin"] == asin].copy()
    if df.empty:
        raise ValueError("所选 ASIN 没有可用行")
    mode = args.mode if args.mode != "auto" else ("daily" if "date" in df else "aggregate")
    if mode == "daily" and "date" not in df:
        raise ValueError("daily 模式需要真实 date 列")
    if mode == "aggregate" and "date" in df:
        raise ValueError("存在逐日 date 列，请使用 daily 模式，避免丢弃时间粒度")
    if mode == "aggregate":
        lo, hi = period_for(path, args.start_date, args.end_date)
        for field, expected in [("Report Window Start", lo), ("Report Window End", hi)]:
            if field in df and any(pd.Timestamp(v) != expected for v in df[field]):
                raise ValueError("声明窗口与源窗口不一致")
    else:
        lo = pd.Timestamp(args.start_date) if args.start_date else df["date"].min()
        hi = pd.Timestamp(args.end_date) if args.end_date else df["date"].max()
        if lo > hi:
            raise ValueError("日期范围无效")
    before_dates = len(df)
    if mode == "daily":
        df = df[(df["date"] >= lo) & (df["date"] <= hi)].copy()
    if df.empty:
        raise ValueError("时间窗内没有记录")
    duplicate = df.drop(columns=["source_file"], errors="ignore").duplicated()
    if duplicate.any() and not args.deduplicate:
        raise ValueError("存在重复记录；核对后可显式使用 --deduplicate")
    df = df.loc[~duplicate].copy()
    thresholds, protected, goal, verified_brands = load_config(args.config)
    brand = args.brand or (metadata["brand_candidates"][0]["brand"] if metadata["brand_candidates"] else None)
    title, context_text, context_source = None, None, None
    if args.live_listing:
        title, context_text, context_source = engine.load_listing_context_live(asin, args.site)
    if args.listing_context_file:
        extra = engine.load_text_file(Path(args.listing_context_file))
        title = title or engine.infer_title_from_context(extra)
        context_text = "\n".join(filter(None, [context_text, extra]))
        context_source = "provided_file:" + Path(args.listing_context_file).name
    brand_tokens = {engine.normalize_token(x) for x in engine.tokenize(brand) if len(x) > 1} if brand else set()
    core = engine.infer_core_tokens(df)
    ctx = engine.AnalysisContext(brand, asin, args.site, args.report_type or metadata["report_type"], args.target_acos, core, brand_tokens,
        {" ".join(brand_name.lower().split()) for brand_name in verified_brands},
        title, context_text, engine.extract_listing_tokens(title, context_text, brand_tokens), context_source, mode,
        "orders" in df and df["orders"].notna().all(), "sales" in df and df["sales"].notna().all(), hi.date().isoformat())
    frame, cvr, acos = engine.build_analysis_frame(df, ctx, thresholds)
    frame = engine.add_decision_columns(frame, ctx, cvr, acos, thresholds)
    if mode == "aggregate":
        frame["trend_flag"] = "not_available_aggregate"
    if not ctx.orders_available or not ctx.sales_available:
        frame["decision_tag"] = "manual_review"
        frame["decision_reason"] = "转化字段缺失或不完整；不能视为零单，不能给控价、否词或放量结论"
    for i, row in frame.iterrows():
        if row["search_term"] in {x.strip().lower() for x in protected} and row["decision_tag"] == "negative_candidate":
            frame.loc[i, ["decision_tag", "decision_reason"]] = ["manual_review", "命中本次明确保护词，否定候选已阻断"]
    entities = source_entities(df)
    frame["source_entities"] = frame["search_term"].map(entities)
    if mode == "aggregate":
        frame = frame.drop(columns=[c for c in frame if c.startswith(("7d_", "14d_"))])
        frame = frame.rename(columns={c: c.replace("30d_", "period_", 1) for c in frame if c.startswith("30d_")})
    counts = frame["decision_tag"].value_counts().to_dict()
    summary = {"status": "DONE_WITH_CONCERNS", "asin": asin, "brand": brand, "site": args.site, "input_mode": mode,
        "start_date": lo.date().isoformat(), "end_date": hi.date().isoformat(), "days": (hi-lo).days + 1,
        "input_rows": len(df), "distinct_search_terms": len(frame), "excluded_other_asin": excluded_asin,
        "excluded_date_rows": before_dates-len(df)-int(duplicate.sum()), "duplicate_rows_removed": int(duplicate.sum()),
        "observed_daily_dates": int(df["date"].nunique()) if mode == "daily" else None,
        "window_coverage_note": "记录中出现的日期数量不证明逐日报表完整" if mode == "daily" else "汇总窗口，不推断7/14/30天趋势",
        "reference_cvr": float(cvr) if ctx.orders_available and df['clicks'].sum()>0 else None, "reference_acos": acos,
        "target_acos": args.target_acos, "goal": goal, "thresholds": thresholds, "protected_keywords": protected,
        "decision_counts": {str(k): int(v) for k,v in counts.items()}, "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "economics_verified": False, "business_writes": 0, "candidate_only": True,
        "orders_complete": bool(ctx.orders_available), "sales_complete": bool(ctx.sales_available)}
    return frame, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--asin")
    parser.add_argument("--brand")
    parser.add_argument("--site", default="US")
    parser.add_argument("--report-type")
    parser.add_argument("--mode", choices=["auto", "daily", "aggregate"], default="auto")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--target-acos", type=float)
    parser.add_argument("--config")
    parser.add_argument("--listing-context-file")
    parser.add_argument("--live-listing", action="store_true", help="显式允许公开页面抓取；不读取浏览器凭据")
    parser.add_argument("--deduplicate", action="store_true")
    args = parser.parse_args()
    if args.target_acos is not None and (not math.isfinite(args.target_acos) or args.target_acos <= 0):
        raise ValueError("target-acos 必须为正比例")
    frame, summary = analyze(args)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    for name in ["details.csv", "candidates.csv", "summary.json", "report.html"]:
        if (out/name).exists():
            raise FileExistsError(f"输出已存在：{name}；请使用新的运行目录")
    frame.to_csv(out/"details.csv", index=False, encoding="utf-8-sig")
    frame[frame["decision_tag"].isin(["negative_candidate", "reduce_bid", "manual_review", "scale_up"])].to_csv(out/"candidates.csv", index=False, encoding="utf-8-sig")
    (out/"summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    public = {k:v for k,v in summary.items() if k not in ["thresholds", "input_sha256"]}
    body = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>搜索词分析</title><style>body{font:16px/1.7 system-ui;max-width:1200px;margin:auto;padding:24px;color:#21334a}table{border-collapse:collapse;font-size:13px}td,th{border:1px solid #ccd4dd;padding:8px;vertical-align:top}section{overflow:auto}pre{white-space:pre-wrap}</style><h1>搜索词分析 · '+html.escape(summary['asin'])+'</h1><p>只读候选报告；参考 ACOS 不是利润线。所有候选仍需结合实际当前状态和产品事实人工复核。</p><pre>'+html.escape(json.dumps(public,ensure_ascii=False,indent=2))+'</pre><section>'+frame.drop(columns=["source_entities"],errors="ignore").to_html(index=False,na_rep="未获取",escape=True)+'</section><p><a href="details.csv">完整明细及投放来源</a> · <a href="candidates.csv">候选清单</a> · <a href="summary.json">运行摘要</a></p></html>'
    (out/"report.html").write_text(body)
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
