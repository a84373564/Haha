import requests
import time
import hmac
import hashlib
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

# 檔案路徑
config_path = Path("~/Killcore/mexc_api_config.json").expanduser()
king_path = Path("~/Killcore/modules/king.json").expanduser()
output_path = Path("~/Killcore/king_performance.json").expanduser()

# 讀入金鑰與模組
cfg = json.loads(config_path.read_text())
king = json.loads(king_path.read_text())
symbol = king["symbol"]
capital = king["capital"]

# 拉 MEXC K 線
def get_klines(symbol, interval="15m", limit=500):
    base_url = "https://api.mexc.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(base_url, params=params)
    return response.json()

# MA 交叉策略
def run_strategy(data, ma_fast, ma_slow, sl_pct, tp_pct, latency=2):
    data["ma_fast"] = data["close"].rolling(ma_fast).mean()
    data["ma_slow"] = data["close"].rolling(ma_slow).mean()
    data.dropna(inplace=True)
    
    in_position = False
    entry_price = 0
    capital_curve = [capital]
    trade_results = []

    for i in range(latency, len(data)):
        row = data.iloc[i]
        prev = data.iloc[i - latency]

        # 進場
        if not in_position and prev["ma_fast"] > prev["ma_slow"]:
            in_position = True
            entry_price = row["open"] * (1 + 0.002)  # 滑價+手續費
            entry_index = i
        elif in_position:
            # 出場邏輯
            sl_price = entry_price * (1 - sl_pct / 100)
            tp_price = entry_price * (1 + tp_pct / 100)
            low = row["low"]
            high = row["high"]
            close = row["close"]

            exit_reason = None
            if low <= sl_price:
                pnl = -capital * (sl_pct / 100 + 0.002)
                exit_reason = "SL"
            elif high >= tp_price:
                pnl = capital * (tp_pct / 100 - 0.002)
                exit_reason = "TP"
            elif i - entry_index > 30:
                pnl = (close - entry_price) / entry_price * capital - (capital * 0.002)
                exit_reason = "timeout"
            else:
                capital_curve.append(capital_curve[-1])
                continue

            trade_results.append(pnl)
            capital_curve.append(capital_curve[-1] + pnl)
            in_position = False

    return trade_results, capital_curve

# 整理資料與績效
raw = get_klines(symbol)
df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume", "ignore"])
df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

params = king["parameters"]
trades, curve = run_strategy(df, params["ma_fast"], params["ma_slow"], params["sl_pct"], params["tp_pct"])

returns = np.array(trades)
if len(returns) == 0:
    output = {
        "return_pct": -100,
        "net_profit": -capital,
        "drawdown": 100,
        "sharpe": -99,
        "win_rate": 0,
        "trade_count": 0,
        "capital_curve": [capital],
        "fail_reason": "無交易",
        "fail_indicators": ["Volume", "RSI"]
    }
else:
    total = np.sum(returns)
    drawdown = max(1 - min(curve) / max(curve), 0) * 100
    win_rate = np.sum(returns > 0) / len(returns) * 100
    sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(12) if np.std(returns) > 0 else -1
    output = {
        "return_pct": round(total / capital * 100, 2),
        "net_profit": round(total, 2),
        "drawdown": round(drawdown, 2),
        "sharpe": round(sharpe, 2),
        "win_rate": round(win_rate, 2),
        "trade_count": len(returns),
        "capital_curve": [round(v, 2) for v in curve],
        "fail_reason": "" if total > 0 else "策略失敗",
        "fail_indicators": ["RSI"] if win_rate < 50 else []
    }

# 寫入績效
output_path.write_text(json.dumps(output, indent=2))
print("[Live Simulator] 完成，績效已寫入 king_performance.json")
