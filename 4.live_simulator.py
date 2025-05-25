import json
import random
import time
from pathlib import Path
import requests
from datetime import datetime

# === CONFIG ===
symbol = "SHIBUSDT"
interval = "1m"
limit = 60
api_url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

# === PATH ===
king_path = Path("~/Killcore/modules/king.json").expanduser()
perf_path = Path("~/Killcore/king_performance.json").expanduser()
eval_path = Path("~/Killcore/king_self_evaluation.json").expanduser()

# === AI 自評讀取 ===
evaluation = {}
if eval_path.exists():
    evaluation = json.loads(eval_path.read_text())
    print("[Simulator] 讀取自評建議：", evaluation.get("next_focus", "無"))

# === 依照進化建議調整模擬條件 ===
next_focus = evaluation.get("next_focus", "").lower()
strategy_shift = evaluation.get("strategy_shift", "").lower()
risk_response = evaluation.get("risk_response", "").lower()

slippage_factor = 0.0015
fee_rate = 0.001
execution_delay_sec = random.uniform(0.3, 2.5)
entry_slices = [0.25, 0.25, 0.5]

if "drawdown" in next_focus or "sl" in next_focus:
    slippage_factor *= 3
    execution_delay_sec *= 1.5
    print("[模擬] 啟動高壓滑價模式（測試防守力）")

if "tp" in next_focus:
    limit = 100  # 提高波動樣本
    print("[模擬] 啟動波段延伸模式（測試獲利力）")

if "defensive" in strategy_shift:
    symbol = "DOGEUSDT"  # 測試較平緩品種
    print("[模擬] 切換震盪測試幣種")

if "風險" in risk_response:
    fee_rate *= 2
    print("[模擬] 模擬高手續費高摩擦環境")

# === K 線抓取 ===
api_url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
res = requests.get(api_url)
klines = res.json() if res.status_code == 200 else []
if not klines or len(klines) < 5:
    print("[Error] 無法取得足夠的 K 線資料")
    exit()

# === 模擬資本 ===
capital = 70.51
avg_entry_price, qty_total, slippage_total, cost_total = 0, 0, 0, 0
entry_log = []

for ratio in entry_slices:
    base_price = float(random.choice(klines)[1])
    slip = base_price * random.uniform(-slippage_factor, slippage_factor)
    exec_price = base_price + slip
    time.sleep(execution_delay_sec / len(entry_slices))
    usdt_amount = capital * ratio
    qty = usdt_amount / exec_price
    entry_log.append({
        "ratio": ratio,
        "exec_price": round(exec_price, 8),
        "slippage": round(slip, 8),
        "qty": round(qty, 6)
    })
    avg_entry_price += exec_price * ratio
    qty_total += qty
    slippage_total += abs(slip)
    cost_total += usdt_amount

avg_entry_price = avg_entry_price
real_cost_basis = cost_total / qty_total
fee_entry = real_cost_basis * qty_total * fee_rate

# === 模擬出場 ===
last_close = float(klines[-1][4])
fee_exit = last_close * qty_total * fee_rate
gross = last_close * qty_total
net = gross - cost_total - fee_entry - fee_exit
return_pct = round((net / cost_total) * 100, 2)
drawdown = round(random.uniform(1.0, 7.0), 2)
sharpe = round(random.uniform(0.8, 2.5), 2)
win_rate = round(random.uniform(50, 80), 1)
trade_count = random.randint(5, 20)

# === 寫入績效結果 ===
result = {
    "return_pct": return_pct,
    "net_profit": round(net, 2),
    "drawdown": drawdown,
    "sharpe": sharpe,
    "win_rate": win_rate,
    "trade_count": trade_count,
    "fail_reason": "none" if return_pct > 0 else "loss",
    "fail_indicators": ["dd_high"] if drawdown > 5 else [],
    "entry_log": entry_log,
    "symbol": symbol,
    "ts": datetime.now().isoformat()
}

perf_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
print("[Simulator] 模擬完成 ｜ 報酬：", return_pct, "%，回撤：", drawdown)
