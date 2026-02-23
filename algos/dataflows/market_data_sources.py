# tushare_common.py

import os
import pandas as pd
import tushare as ts
from datetime import datetime
from io import StringIO
from typing import Optional


# =========================
# Tushare 全局初始化控制
# =========================

_PRO: Optional[ts.pro_api] = None


def _initialize_tushare():
    """
    Initialize Tushare token exactly once.
    """
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise ValueError(
            "TUSHARE_TOKEN environment variable is not set."
        )
    ts.set_token(token)


def get_pro():
    """
    Lazily get a Tushare Pro API client.
    Ensures token initialization happens before use.
    """
    global _PRO
    if _PRO is None:
        _initialize_tushare()
        _PRO = ts.pro_api()
    return _PRO


# =========================
# 时间格式工具
# =========================

def format_date_for_api(date_input) -> str:
    """
    Convert various date formats to YYYYMMDD format required by Tushare API.
    """
    if isinstance(date_input, str):
        try:
            dt = datetime.strptime(date_input, "%Y-%m-%d")
            return dt.strftime("%Y%m%d")
        except ValueError:
            raise ValueError(f"Unsupported date format: {date_input}")
    elif isinstance(date_input, datetime):
        return date_input.strftime("%Y%m%d")
    else:
        raise ValueError(
            f"Date must be string or datetime object, got {type(date_input)}"
        )


# =========================
# A 股行情数据
# =========================

def get_a_share_daily(
    ts_code: str,
    start_date: str,
    end_date: str
) -> str:
    """
    Get A-share daily price data.
    """
    pro = get_pro()

    start = format_date_for_api(start_date)
    end = format_date_for_api(end_date)

    df = pro.daily(
        ts_code=ts_code,
        start_date=start,
        end_date=end
    )

    if df.empty:
        return ""

    df = df.sort_values("trade_date")
    return df.to_csv(index=False)


def get_a_share_index_daily(
    ts_code: str,
    start_date: str,
    end_date: str
) -> str:
    """
    Get A-share index daily data.
    """
    pro = get_pro()

    start = format_date_for_api(start_date)
    end = format_date_for_api(end_date)

    df = pro.index_daily(
        ts_code=ts_code,
        start_date=start,
        end_date=end
    )

    if df.empty:
        return ""

    df = df.sort_values("trade_date")
    return df.to_csv(index=False)



# =========================
# CSV 时间区间过滤
# =========================

def filter_csv_by_date_range(
    csv_data: str,
    start_date: str,
    end_date: str
) -> str:
    """
    Filter CSV data to include only rows within the specified date range.
    """
    if not csv_data or csv_data.strip() == "":
        return csv_data

    try:
        df = pd.read_csv(StringIO(csv_data))
        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col])

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        filtered_df = df[
            (df[date_col] >= start_dt) &
            (df[date_col] <= end_dt)
        ]

        return filtered_df.to_csv(index=False)

    except Exception as e:
        print(
            f"Warning: Failed to filter CSV data by date range: {e}"
        )
        return csv_data


