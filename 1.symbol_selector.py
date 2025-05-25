import requests
import json
from pathlib import Path

API_URL = "https://api.mexc.com"
SYMBOLS = ["DOGEUSDT", "SHIBUSDT"]
symbol_score = {}

# 記憶權重讀取（如無則為 0）
memory_path = Path("~/Killcore/king_memory.json").expanduser()
memory = {}
if memory_path.exists():
    try:
        memory = json.loads(memory_path.read_text())
    except json.JSONDecodeError as e:
        print(f"[錯誤] king_memory.json 無法解析：{e}")
        raise

for symbol in SYMBOLS:
    try:
        r = requests.get(f"{API_URL}/api/v3/ticker/24hr?symbol={symbol}", timeout=10)
        r.raise_for_status()
        data = r.json()
        vol = float(data.get("quoteVolume", 0))
        chg = abs(float(data.get("priceChangePercent", 0)))
        mem_score = memory.get(symbol, {}).get("score", 0)
        total = round(chg * 5 + vol / 1e7 + mem_score, 2)
        symbol_score[symbol] = {
            "vol": round(vol / 1e6, 2),
            "chg": round(chg, 2),
            "mem": round(mem_score, 2),
            "total": total
        }
    except Exception as e:
        print(f"[錯誤] 無法獲取幣種 {symbol}：{e}")
        raise

# 排名
sorted_symbols = sorted(symbol_score.items(), key=lambda x: x[1]["total"], reverse=True)
selected = sorted_symbols[0][0]

# 顯示結果
print("\n[Symbol Selector v1.1]")
for sym, s in sorted_symbols:
    print(f"{sym.ljust(10)}｜ 波動: {s['chg']}% ｜ 成交量: {s['vol']}M ｜ 記憶分數: {s['mem']} ｜ 總分: {s['total']}")
print(f"\n>>> 本輪建議交易幣種: {selected}")

# 儲存 symbol 給核心模組使用
symbol_path = Path("~/Killcore/selected_symbol.json").expanduser()
symbol_path.write_text(json.dumps({"symbol": selected}, indent=2))
