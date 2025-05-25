import json
from pathlib import Path
from datetime import datetime

# 路徑
king_path = Path("~/Killcore/modules/king.json").expanduser()
perf_path = Path("~/Killcore/king_performance.json").expanduser()
mem_path = Path("~/Killcore/king_memory.json").expanduser()

# 檢查來源資料
if not king_path.exists() or not perf_path.exists():
    raise FileNotFoundError("king.json 或 king_performance.json 缺失")

king = json.loads(king_path.read_text())
perf = json.loads(perf_path.read_text())

# 載入或建立記憶體
if mem_path.exists():
    try:
        memory = json.loads(mem_path.read_text())
    except json.JSONDecodeError as e:
        print(f"[錯誤] king_memory.json 解析失敗: {e}")
        raise
else:
    memory = {
        "live_rounds": 0,
        "fail_indicators_count": {},
        "history": [],
        "style_profile": None,
        "learning_score": 0,
        "memory_flags": {},
        "aging_map": {},
        "fail_pattern_stats": {},
        "evolution_trace": []
    }

# 更新 live_rounds
memory["live_rounds"] += 1

# 統計 fail_indicators
for f in perf.get("fail_indicators", []):
    memory["fail_indicators_count"][f] = memory["fail_indicators_count"].get(f, 0) + 1

# 建立本輪紀錄
this_round = {
    "ts": datetime.now().isoformat(),
    "return_pct": perf.get("return_pct"),
    "net_profit": perf.get("net_profit"),
    "drawdown": perf.get("drawdown"),
    "win_rate": perf.get("win_rate"),
    "sharpe": perf.get("sharpe"),
    "trade_count": perf.get("trade_count"),
    "fail_reason": perf.get("fail_reason", ""),
    "symbol": king.get("symbol"),
    "params": king.get("parameters"),
    "intent": king.get("evolution_intent", []),
    "score_snapshot": {
        "bias": king.get("init_bias_score"),
        "temp": king.get("temperature_level"),
        "risk_tol": king.get("risk_tolerance"),
    }
}
memory["history"].append(this_round)

# 推測 style_profile（簡化：根據 TP/SL 判斷）
tp = king["parameters"].get("tp_pct", 5)
sl = king["parameters"].get("sl_pct", 2)
style = "explosive" if tp > 8 else "defensive" if sl < 2 else "balanced"
memory["style_profile"] = style

# 壞習慣偵測（失敗指標 > 10 次則封印）
for f, count in memory["fail_indicators_count"].items():
    if count >= 10:
        memory["memory_flags"][f] = "封印候選"

# 記憶衰退地圖（只保留最近 30 輪，其他標記為過期）
if len(memory["history"]) > 30:
    for i, h in enumerate(memory["history"][:-30]):
        memory["aging_map"][i] = "過期"
    memory["history"] = memory["history"][-30:]

# 學習指數（過去 5 輪正報酬次數）
recent = memory["history"][-5:]
memory["learning_score"] = sum(1 for r in recent if r["return_pct"] > 0)

# 更新進化摘要（evolution_trace）
evo = {
    "generation": king.get("generation"),
    "ts": datetime.now().isoformat(),
    "intent": king.get("evolution_intent", []),
    "result": f'{perf.get("return_pct", 0)}% / {perf.get("drawdown", 0)}% DD'
}
memory["evolution_trace"].append(evo)

# 寫入記憶
mem_path.write_text(json.dumps(memory, indent=2))
print(f"[Memory Recorder] 第 {memory['live_rounds']} 輪記憶完成：fail_total={sum(memory['fail_indicators_count'].values())}，風格={memory['style_profile']}，學習力={memory['learning_score']}")
