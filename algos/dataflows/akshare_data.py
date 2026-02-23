# 股票数据接口 - 使用 akshare 获取当日行情和技术因子
# pip install akshare pandas numpy

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Union


class StockDataAPI:
    """
    股票数据接口类，提供当日行情和技术因子数据
    """
    
    def __init__(self):
        self.today = datetime.now().strftime("%Y%m%d")
        self.last_30_days = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    
    def get_stock_data(self, symbol: str) -> Dict[str, Union[pd.DataFrame, Dict]]:
        """
        获取股票当日行情和技术因子数据
        
        Args:
            symbol: 股票代码（如 "600000" 或 "000001"）
            
        Returns:
            Dict: 包含行情数据和因子数据的字典
        """
        try:
            # 验证股票代码格式
            symbol = self._validate_symbol(symbol)
            
            # 获取历史数据（最近30天，用于计算因子）
            hist_data = self._get_historical_data(symbol)
            
            # 获取当日行情
            daily_data = self._get_daily_data(symbol)
            
            # 计算技术因子
            factors = self._calculate_factors(hist_data)
            
            return {
                "symbol": symbol,
                "daily_data": daily_data,
                "factors": factors,
                "historical_data": hist_data.tail(10)  # 返回最近10天数据
            }
            
        except Exception as e:
            return {
                "symbol": symbol,
                "error": f"获取数据失败: {str(e)}",
                "daily_data": pd.DataFrame(),
                "factors": {},
                "historical_data": pd.DataFrame()
            }
    
    def _validate_symbol(self, symbol: str) -> str:
        """验证并格式化股票代码"""
        if not symbol:
            raise ValueError("股票代码不能为空")
        
        # 移除可能的交易所前缀
        symbol = symbol.replace(".SH", "").replace(".SZ", "")
        
        # 验证是否为6位数字
        if not symbol.isdigit() or len(symbol) != 6:
            raise ValueError(f"股票代码格式错误: {symbol}")
        
        return symbol
    
    def _get_historical_data(self, symbol: str) -> pd.DataFrame:
        """获取最近30天的历史数据"""
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=self.last_30_days,
            end_date=self.today,
            adjust="qfq"
        )
        
        if df.empty:
            raise ValueError(f"未找到股票 {symbol} 的历史数据")
        
        # 确保日期列是datetime类型
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期')
        
        return df
    
    def _get_daily_data(self, symbol: str) -> pd.DataFrame:
        """获取当日行情数据"""
        # 获取实时行情
        realtime_data = ak.stock_zh_a_spot_em()
        
        # 过滤指定股票
        stock_data = realtime_data[realtime_data['代码'] == symbol]
        
        if stock_data.empty:
            # 如果实时数据没有，尝试从历史数据获取最新一天
            hist_data = self._get_historical_data(symbol)
            latest_data = hist_data.iloc[-1:]
            
            # 重命名列以匹配实时数据格式
            latest_data = latest_data.rename(columns={
                '日期': '日期',
                '开盘': '今开',
                '收盘': '最新价',
                '最高': '最高',
                '最低': '最低',
                '成交量': '成交量',
                '成交额': '成交额',
                '振幅': '振幅',
                '涨跌幅': '涨跌幅',
                '涨跌额': '涨跌额',
                '换手率': '换手率'
            })
            
            return latest_data
        
        return stock_data
    
    def _calculate_factors(self, hist_data: pd.DataFrame) -> Dict[str, float]:
        """计算技术因子"""
        if len(hist_data) < 5:
            return {}
        
        close_prices = hist_data['收盘'].astype(float)
        high_prices = hist_data['最高'].astype(float)
        low_prices = hist_data['最低'].astype(float)
        volumes = hist_data['成交量'].astype(float)
        
        factors = {}
        
        # 1. 移动平均线
        factors['MA5'] = close_prices.tail(5).mean()
        factors['MA10'] = close_prices.tail(10).mean()
        factors['MA20'] = close_prices.tail(20).mean()
        
        # 2. 相对强弱指数 (RSI)
        factors['RSI14'] = self._calculate_rsi(close_prices, 14)
        
        # 3. MACD
        macd_data = self._calculate_macd(close_prices)
        factors.update(macd_data)
        
        # 4. 布林带
        bollinger_data = self._calculate_bollinger_bands(close_prices)
        factors.update(bollinger_data)
        
        # 5. 成交量相关因子
        factors['Volume_MA5'] = volumes.tail(5).mean()
        factors['Volume_Ratio'] = volumes.iloc[-1] / volumes.tail(5).mean() if volumes.tail(5).mean() > 0 else 0
        
        # 6. 价格动量
        factors['Momentum_5'] = (close_prices.iloc[-1] / close_prices.iloc[-6] - 1) * 100
        factors['Momentum_10'] = (close_prices.iloc[-1] / close_prices.iloc[-11] - 1) * 100
        
        return factors
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return 50.0  # 默认值
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def _calculate_macd(self, prices: pd.Series) -> Dict[str, float]:
        """计算MACD指标"""
        if len(prices) < 26:
            return {'MACD': 0, 'MACD_Signal': 0, 'MACD_Histogram': 0}
        
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return {
            'MACD': round(macd.iloc[-1], 4),
            'MACD_Signal': round(signal.iloc[-1], 4),
            'MACD_Histogram': round(histogram.iloc[-1], 4)
        }
    
    def _calculate_bollinger_bands(self, prices: pd.Series) -> Dict[str, float]:
        """计算布林带指标"""
        if len(prices) < 20:
            return {'BB_Middle': 0, 'BB_Upper': 0, 'BB_Lower': 0, 'BB_Width': 0}
        
        middle = prices.rolling(window=20).mean()
        std = prices.rolling(window=20).std()
        upper = middle + 2 * std
        lower = middle - 2 * std
        width = (upper - lower) / middle
        
        return {
            'BB_Middle': round(middle.iloc[-1], 2),
            'BB_Upper': round(upper.iloc[-1], 2),
            'BB_Lower': round(lower.iloc[-1], 2),
            'BB_Width': round(width.iloc[-1] * 100, 2)  # 百分比形式
        }


def get_stock_info(symbol: str) -> Dict[str, Union[pd.DataFrame, Dict]]:
    """
    便捷函数：获取股票数据的简化接口
    
    Args:
        symbol: 股票代码
        
    Returns:
        Dict: 股票数据字典
    """
    api = StockDataAPI()
    return api.get_stock_data(symbol)


# 使用示例
if __name__ == "__main__":
    # 创建API实例
    api = StockDataAPI()
    
    # 测试不同股票
    test_symbols = ["600000"]
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"获取股票 {symbol} 的数据")
        print(f"{'='*60}")
        
        result = api.get_stock_data(symbol)
        
        if "error" in result:
            print(f"错误: {result['error']}")
            continue
        
        # 显示当日行情
        print("\n当日行情:")
        if not result['daily_data'].empty:
            daily = result['daily_data'].iloc[0]
            print(f"  最新价: {daily.get('最新价', 'N/A')}")
            print(f"  涨跌幅: {daily.get('涨跌幅', 'N/A')}%")
            print(f"  成交量: {daily.get('成交量', 'N/A')}")
            print(f"  成交额: {daily.get('成交额', 'N/A')}")
        
        # 显示技术因子
        print("\n技术因子:")
        for factor, value in result['factors'].items():
            print(f"  {factor}: {value}")
        
        # 显示最近几天历史数据
        print(f"\n最近{len(result['historical_data'])}天历史数据:")
        print(result['historical_data'][['日期', '开盘', '收盘', '涨跌幅', '成交量']].to_string(index=False))