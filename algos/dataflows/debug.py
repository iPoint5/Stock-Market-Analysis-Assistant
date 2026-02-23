from tushare_common import get_a_share_daily
if __name__ == "__main__":
    """
    主函数，用于测试和演示获取A股数据的功能
    """
    import sys
    
    # 默认参数
    default_ts_code = "600000.SH"  # 浦发银行
    default_start_date = "2023-01-01"
    default_end_date = "2023-01-31"
    
    # 获取命令行参数
    if len(sys.argv) == 4:
        ts_code = sys.argv[1]
        start_date = sys.argv[2]
        end_date = sys.argv[3]
    else:
        # 使用默认参数
        ts_code = default_ts_code
        start_date = default_start_date
        end_date = default_end_date
        print(f"使用默认参数: 股票代码={ts_code}, 开始日期={start_date}, 结束日期={end_date}")
    
    print("=" * 80)
    print(f"获取股票 {ts_code} 的数据")
    print(f"时间区间: {start_date} 到 {end_date}")
    print("=" * 80)
    
    # 1. 获取每日行情数据
    print("\n1. 每日行情数据:")
    print("-" * 60)
    daily_data = get_a_share_daily(ts_code, start_date, end_date)
    if daily_data:
        print(daily_data)
    else:
        print("未获取到每日行情数据")


