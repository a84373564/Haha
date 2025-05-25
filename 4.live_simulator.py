import requests
import json
import pandas as pd
import numpy as np
from pathlib import Path

# 路徑設定
config_path = Path("~/Killcore/mexc_api_config.json").expanduser()
king_path = Path("~/Killcore/modules/king.json").expanduser()
output_path = Path("~/Killcore/king_performance.json").expanduser()

# 讀入設定
cfg = json.loads(config_path.read_text())
king = json.loads(king_path.read_text())
symbol = king["symbol"]
capital = king["capital"]

# 抓取 MEXC 歷史 K 線
def get_klines(symbol, interval="15m", limit=500):
    url = "https://api.mexc.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    return response.json()

# MA 策略模擬器
def run_strategy(df, ma_fast, ma_slow, sl_pct, tp_pct, latency=2):
    df["ma_fast"] = df["close"].rolling(ma_fast).mean()
    df["ma_slow"] = df["close"].rolling(ma_slow).mean()
    df.dropna(inplace=True)

    in_position = False
    entry_price = 0
    capital_curve = [capital]
    trades = []

    for i in range(latency, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - latency]

        # 進場邏輯
        if not in_position and prev["ma_fast"] > prev["ma_slow"]:
            in_position = True
            entry_price = row["open"] * (1 + 0.002)  # 滑價 + 手續費
            entry_index = i
        elif in_position:
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
                pnl = (close - entry_price) / entry_price * capital - capital * 0.002
                exit_reason = "timeout"
            else:
                capital_curve.append(capital_curve[-1])
                continue

            trades.append(pnl)
            capital_curve.append(capital_curve[-1] + pnl)
            in_position = False

    return trades, capital_curve

# 擷取資料
raw = get_klines(symbol)
df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume", "close_time", "ignore"])
df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

# 參數
params = king["parameters"]
trades, curve = run_strategy(df, params["ma_fast"], params["ma_slow"], params["sl_pct"], params["tp_pct"])

# 統計績效
returns = np.array(trades)
if len(returns) == 0:
    result = {
        "return_pct": -100,
        "net_profit": -capital,
        "drawdown": 100,
        "sharpe": -99,
        "win_rate": 0,
        "trade_count": 0,
        "capital_curve": [capital],
        "fail_reason": "無交易",
        "fail_indicators": ["RSI", "Volume"]
    }
else:
    total = np.sum(returns)
    drawdown = round((1 - min(curve) / max(curve)) * 100, 2)
    win_rate = round(np.sum(returns > 0) / len(returns) * 100, 2)
    sharpe = round((np.mean(returns) / np.std(returns)) * np.sqrt(12), 2) if np.std(returns) > 0 else -1
    result = {
        "return_pct": round(total / capital * 100, 2),
        "net_profit": round(total, 2),
        "drawdown": drawdown,
        "sharpe": sharpe,
        "win_rate": win_rate,
        "trade_count": len(returns),
        "capital_curve": [round(x, 2) for x in curve],
        "fail_reason": "" if total > 0 else "策略失敗",
        "fail_indicators": ["RSI"] if win_rate < 50 else []
    }

# 寫出績效
output_path.write_text(json.dumps(result, indent=2))
print("[Live Simulator] 模擬完成，績效已寫入 king_performance.json")
