import json
import requests
from pathlib import Path

# 配置區
SYMBOLS = ["SHIBUSDT", "DOGEUSDT"]
memory_file = Path("~/Killcore/symbol_memory.json").expanduser()
API_BASE = "https://api.mexc.com"

# 初始化記憶檔
if not MEMORY_FILE.exists():
    memory = {s: {"uses": 0, "avg_return": 0.0} for s in SYMBOLS}
    MEMORY_FILE.write_text(json.dumps(memory, indent=2))
else:
    memory = json.loads(MEMORY_FILE.read_text())

# 擷取幣種波動與成交量
def fetch_symbol_data(symbol):
    url = f"{API_BASE}/api/v3/ticker/24hr?symbol={symbol}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        high = float(data["highPrice"])
        low = float(data["lowPrice"])
        vol = float(data["quoteVolume"])
        volatility = (high - low) / low * 100 if low > 0 else 0
        return round(volatility, 2), round(vol / 1_000_000, 2)
    except Exception:
        return 0.0, 0.0

# 打分選擇最佳幣種
results = []
for sym in SYMBOLS:
    vol, vol_usdt = fetch_symbol_data(sym)
    mem_score = memory[sym]["avg_return"]
    score = vol * 0.5 + vol_usdt * 0.3 + mem_score * 0.2
    results.append({
        "symbol": sym,
        "volatility": vol,
        "volume_m_usdt": vol_usdt,
        "memory_score": mem_score,
        "score": round(score, 2)
    })

# 排序選擇
results.sort(key=lambda x: x["score"], reverse=True)
chosen = results[0]["symbol"]

# 輸出與儲存選擇記錄
print("\n[Symbol Selector v1]")
for r in results:
    print(f"{r['symbol']} | 波動: {r['volatility']}% | 成交量: {r['volume_m_usdt']}M | 記憶分數: {r['memory_score']} | 總分: {r['score']}")

print(f"\n>>> 本輪建議交易幣種：{chosen}")

# 儲存記憶檔（使用次數+1）
memory[chosen]["uses"] += 1
MEMORY_FILE.write_text(json.dumps(memory, indent=2))
