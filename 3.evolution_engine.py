import json
import random
from datetime import datetime
from pathlib import Path

# 路徑設定
king_path = Path("~/Killcore/modules/king.json").expanduser()
perf_path = Path("~/Killcore/king_performance.json").expanduser()
mem_path = Path("~/Killcore/king_memory.json").expanduser()
market_path = Path("~/Killcore/market_status.json").expanduser()

# 載入資料
king = json.loads(king_path.read_text())
perf = json.loads(perf_path.read_text())
memory = json.loads(mem_path.read_text()) if mem_path.exists() else {}
market = json.loads(market_path.read_text()) if market_path.exists() else {}

# === 預設保護 ===
memory.setdefault("evolution_trace", [])
memory.setdefault("live_rounds", 0)
memory.setdefault("learning_score", 0)
memory.setdefault("style_history", [])
memory.setdefault("drift_history", [])

# === 進化代數提升 ===
king["generation"] += 1
intent_summary = []
style_change = None

# === 市況判斷 ===
vol = market.get("btc_volatility", 0)
trend = market.get("trend_score", 0)
if trend > 0.6 and vol > 5:
    market_type = "trend"
elif vol > 6:
    market_type = "volatile"
elif trend < 0.4:
    market_type = "sideway"
else:
    market_type = "stable"

# === 對應演化行為 ===
style = king.get("style_profile", "balanced")
if market_type == "trend":
    king["parameters"]["tp_pct"] *= 1.1
    style = "explosive"
    intent_summary.append("趨勢市 → 提升 TP% 並採爆發風格")
elif market_type == "sideway":
    king["parameters"]["sl_pct"] *= 0.9
    style = "defensive"
    intent_summary.append("震盪市 → 降低 SL% 並採防守風格")
elif market_type == "volatile":
    king["risk_tolerance"] = min(king.get("risk_tolerance", 0.5) + 0.05, 1.0)
    intent_summary.append("高波動市 → 提高風險容忍")
else:
    intent_summary.append("穩定市 → 保持風格")

# === 偵測風格變化 ===
if king.get("style_profile") != style:
    style_change = f"{king['style_profile']} → {style}"
    king["style_profile"] = style
memory["style_history"].append(style)

# === 偏誤與溫度進化 ===
bias_shift = round(random.uniform(-0.1, 0.1), 2)
king["init_bias_score"] = round(king.get("init_bias_score", 0.0) + bias_shift, 2)
king["temperature_level"] = round(min(max(king.get("temperature_level", 0.5) + random.uniform(-0.05, 0.1), 0), 1), 2)

# === 情緒推論 ===
if perf.get("return_pct", 0) < 0 and perf.get("drawdown", 0) > 3:
    king["emotional_tendency"] = "anxious"
elif perf.get("return_pct", 0) > 0 and perf.get("win_rate", 0) > 60:
    king["emotional_tendency"] = "confident"
else:
    king["emotional_tendency"] = "neutral"

# === 懲罰失敗因子 ===
fail_indicators = perf.get("fail_indicators", [])
for i in fail_indicators:
    if i in king.get("decision_weighting_map", {}):
        king["decision_weighting_map"][i] *= 0.9
        intent_summary.append(f"懲罰失敗因子：{i}")

# === 行為標籤記錄 ===
bad_behavior = []
if perf.get("drawdown", 0) > 6:
    bad_behavior.append("高回撤")
if perf.get("trade_count", 0) > 20:
    bad_behavior.append("過度交易")
if perf.get("win_rate", 100) < 30:
    bad_behavior.append("進場錯誤")

# === 意圖與標籤寫入 king 模組 ===
if not intent_summary:
    intent_summary = ["本輪未產生特定演化意圖"]
king["evolution_intent"] = intent_summary
king["bad_behavior_tag"] = bad_behavior

# === 記錄進化痕跡到記憶 ===
memory["evolution_trace"].append({
    "generation": king["generation"],
    "intent": intent_summary,
    "bias_shift": bias_shift,
    "risk_tolerance": king.get("risk_tolerance"),
    "market_type": market_type,
    "style_profile": king.get("style_profile"),
    "style_change": style_change,
    "emotional_tendency": king["emotional_tendency"],
    "timestamp": datetime.now().isoformat()
})

# === 儲存結果 ===
king_path.write_text(json.dumps(king, indent=2, ensure_ascii=False))
mem_path.write_text(json.dumps(memory, indent=2, ensure_ascii=False))

# === CLI 輸出 ===
print(f"[OK] king 進化至第 {king['generation']} 代 | 市況：{market_type}")
for intent in intent_summary:
    print(" -", intent)
if bad_behavior:
    print(" [!] 壞習慣標記：", ", ".join(bad_behavior))
