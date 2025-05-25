import json
import requests
from pathlib import Path

# 正確記憶檔路徑
MEMORY_FILE = Path("~/Killcore/symbol_memory.json").expanduser()
SYMBOLS = ["SHIBUSDT", "DOGEUSDT"]
API_URL = "https://api.mexc.com"

# 初始化記憶
if not MEMORY_FILE.exists():
    memory = {s: {"uses": 0, "avg_return": 0.0} for s in SYMBOLS}
    MEMORY_FILE.write_text(json.dumps(memory, indent=2))
else:
    memory = json.loads(MEMORY_FILE.read_text())

def fetch(symbol):
    try:
        r = requests.get(f"{API_URL}/api/v3/ticker/24hr?symbol={symbol}", timeout=10)
        d = r.json()
        high, low = float(d["highPrice"]), float(d["lowPrice"])
        vol = float(d["quoteVolume"])
        volatility = (high - low) / low * 100 if low > 0 else 0
        return round(volatility, 2), round(vol / 1_000_000, 2)
    except:
        return 0.0, 0.0

results = []
for sym in SYMBOLS:
    vol, v_usdt = fetch(sym)
    mem = memory[sym]["avg_return"]
    score = vol * 0.5 + v_usdt * 0.3 + mem * 0.2
    results.append({
        "symbol": sym,
        "volatility": vol,
        "volume_m_usdt": v_usdt,
        "memory_score": mem,
        "score": round(score, 2)
    })

results.sort(key=lambda x: x["score"], reverse=True)
chosen = results[0]["symbol"]
memory[chosen]["uses"] += 1
MEMORY_FILE.write_text(json.dumps(memory, indent=2))

print("\n[Symbol Selector v1]")
for r in results:
    print(f"{r['symbol']} | 波動: {r['volatility']}% | 成交量: {r['volume_m_usdt']}M | 記憶分數: {r['memory_score']} | 總分: {r['score']}")
print(f"\n>>> 本輪建議交易幣種：{chosen}")
