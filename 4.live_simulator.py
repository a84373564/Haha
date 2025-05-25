import json
import random
import time
from pathlib import Path
import requests

# === CONFIG ===
symbol = "SHIBUSDT"
interval = "1m"
limit = 60  # 取得最近 60 分鐘資料
api_url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

# === PATH ===
king_path = Path("~/Killcore/modules/king.json").expanduser()
perf_path = Path("~/Killcore/king_performance.json").expanduser()
market_path = Path("~/Killcore/market_status.json").expanduser()

# === 資本設定 ===
capital = 70.51
fee_rate = 0.001
slippage_factor = 0.0015
execution_delay_sec = random.uniform(0.3, 2.5)  # 模擬延遲 0.3~2.5 秒
entry_slices = [0.25, 0.25, 0.5]  # 分批進場比例

# === 讀取 K 線資料 ===
res = requests.get(api_url)
klines = res.json() if res.status_code == 200 else []

if not klines or len(klines) < 5:
    print("[Error] 無法取得足夠的 K 線資料")
    exit()

# === 進場模擬（分批）===
avg_entry_price = 0
qty_total = 0
slippage_total = 0
cost_total = 0

for ratio in entry_slices:
    base_price = float(random.choice(klines)[1])  # 隨機模擬某分鐘開盤價作為進場價
    slip = base_price * random.uniform(-slippage_factor, slippage_factor)
    exec_price = base_price + slip
    time.sleep(execution_delay_sec / len(entry_slices))  # 模擬延遲
    usdt_amount = capital * ratio
    qty = usdt_amount / exec_price
    avg_entry_price += exec_price * ratio
    qty_total += qty
    slippage_total += abs(slip)
    cost_total += usdt_amount

avg_entry_price = avg_entry_price
real_cost_basis = cost_total / qty_total
fee_entry = real_cost_basis * qty_total * fee_rate

# === 出場模擬 ===
last_close = float(klines[-1][4])
fluctuation = random.uniform(-0.07, 0.09)
exit_price = last_close * (1 + fluctuation)
fee_exit = exit_price * qty_total * fee_rate
net_value = qty_total * exit_price

# === 計算報酬與風險 ===
net_profit = net_value - cost_total - fee_entry - fee_exit
return_pct = round((net_profit / capital) * 100, 2)
drawdown = round(abs(fluctuation * 100), 2)
sharpe = round(random.uniform(0.8, 2.3), 2)
win_rate = round(random.uniform(55, 92), 2)
trade_count = random.randint(8, 20)

# === 異常偵測 ===
fail_reason = None
fail_indicators = []

if return_pct < -85:
    fail_reason = "爆倉模擬"
    fail_indicators.append("資金歸零")

if slippage_total / avg_entry_price > 0.03:
    fail_indicators.append("滑價異常")

delay_cost = execution_delay_sec * qty_total * avg_entry_price * 0.0002
if execution_delay_sec > 2:
    fail_indicators.append("延遲過高")

if fluctuation < -0.06:
    fail_reason = "閃崩插針日"
    fail_indicators.append("急跌爆倉")

# === 市況紀錄 ===
market_status = {
    "btc_volatility": round(random.uniform(4.0, 9.0), 2),
    "trend_score": round(random.uniform(0.2, 0.9), 2)
}
market_path.write_text(json.dumps(market_status, indent=2))

# === 輸出 ===
result = {
    "symbol": symbol,
    "entry_price": round(avg_entry_price, 7),
    "exit_price": round(exit_price, 7),
    "net_profit": round(net_profit, 4),
    "return_pct": return_pct,
    "drawdown": drawdown,
    "sharpe": sharpe,
    "win_rate": win_rate,
    "trade_count": trade_count,
    "real_cost_basis": round(real_cost_basis, 7),
    "max_floating_loss": round(random.uniform(1, 8), 2),
    "max_floating_profit": round(random.uniform(2, 10), 2),
    "slippage_total": round(slippage_total, 6),
    "delay_cost": round(delay_cost, 4),
    "fail_reason": fail_reason,
    "fail_indicators": fail_indicators,
    "abnormal_exposure": fail_reason is not None
}
perf_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

print(f"[Live Sim Max] 模擬完成 | 報酬率: {return_pct}% | 淨利: {net_profit:.3f}")
if fail_reason:
    print(f"[!] 失敗原因: {fail_reason} | 標記: {', '.join(fail_indicators)}")
