import json
from pathlib import Path
from datetime import datetime

# 路徑
king_path = Path("~/Killcore/modules/king.json").expanduser()
perf_path = Path("~/Killcore/king_performance.json").expanduser()
mem_path = Path("~/Killcore/king_memory.json").expanduser()

# 載入模組、績效、記憶體
king = json.loads(king_path.read_text())
perf = json.loads(perf_path.read_text())
memory = {}
if mem_path.exists():
    try:
        memory = json.loads(mem_path.read_text())
    except json.JSONDecodeError:
        print("[警告] 無法解析記憶體檔案，將重建記憶。")
        memory = {}

# 初始化結構
memory.setdefault("live_rounds", 0)
memory.setdefault("fail_indicators_count", {})
memory.setdefault("history", [])
memory.setdefault("style_profile", None)
memory.setdefault("learning_score", 0)
memory.setdefault("memory_flags", {})
memory.setdefault("aging_map", {})
memory.setdefault("fail_pattern_stats", {})
memory.setdefault("evolution_trace", [])
memory.setdefault("bad_behavior_tag", [])
memory.setdefault("drift_history", [])
memory.setdefault("intent_summary", [])

# 增加 live_rounds
memory["live_rounds"] += 1

# 累計失敗因子次數
for f in perf.get("fail_indicators", []):
    memory["fail_indicators_count"][f] = memory["fail_indicators_count"].get(f, 0) + 1
    if memory["fail_indicators_count"][f] >= 10:
        memory["memory_flags"][f] = "封印候選"

# 記錄本輪紀錄
round_record = {
    "ts": datetime.now().isoformat(),
    "return_pct": perf.get("return_pct"),
    "net_profit": perf.get("net_profit"),
    "drawdown": perf.get("drawdown"),
    "win_rate": perf.get("win_rate"),
    "sharpe": perf.get("sharpe"),
    "trade_count": perf.get("trade_count"),
    "fail_reason": perf.get("fail_reason"),
    "fail_indicators": perf.get("fail_indicators"),
    "symbol": king.get("symbol"),
    "params": king.get("parameters"),
    "style": king.get("style_profile"),
    "intent": king.get("evolution_intent", []),
    "score_snapshot": {
        "bias": king.get("init_bias_score"),
        "temp": king.get("temperature_level"),
        "risk_tol": king.get("risk_tolerance"),
        "emotion": king.get("emotional_tendency")
    }
}
memory["history"].append(round_record)

# aging_map 標記過期資料
if len(memory["history"]) > 30:
    for i in range(len(memory["history"]) - 30):
        memory["aging_map"][i] = "過期"
    memory["history"] = memory["history"][-30:]

# 學習指數（最近 5 輪正報酬）
recent = memory["history"][-5:]
memory["learning_score"] = sum(1 for r in recent if r.get("return_pct", 0) > 0)

# 風格推估（根據 TP / SL 比例）
tp = king.get("parameters", {}).get("tp_pct", 5)
sl = king.get("parameters", {}).get("sl_pct", 2)
if tp > 8:
    memory["style_profile"] = "explosive"
elif sl < 2:
    memory["style_profile"] = "defensive"
else:
    memory["style_profile"] = "balanced"

# 壞習慣偵測與標記
tags = set(memory.get("bad_behavior_tag", []))
if perf.get("drawdown", 0) > 6:
    tags.add("高回撤")
if perf.get("trade_count", 0) > 20:
    tags.add("過度交易")
if perf.get("win_rate", 100) < 35:
    tags.add("勝率崩盤")
if perf.get("fail_reason"):
    tags.add("重大失誤")
memory["bad_behavior_tag"] = list(tags)

# 進化摘要與人格傾向記錄
evo = {
    "generation": king.get("generation"),
    "ts": datetime.now().isoformat(),
    "intent": king.get("evolution_intent", []),
    "result": f'{perf.get("return_pct", 0)}% / DD {perf.get("drawdown", 0)}%',
    "style": king.get("style_profile"),
    "emotion": king.get("emotional_tendency"),
    "bias": king.get("init_bias_score")
}
memory["evolution_trace"].append(evo)
memory["intent_summary"].extend(king.get("evolution_intent", []))

# 風格漂移偵測
style_set = set(e["style"] for e in memory["evolution_trace"][-3:] if "style" in e)
memory["style_drift_flag"] = len(style_set) > 1
memory["drift_history"].append(list(style_set))

# 寫入記憶
mem_path.write_text(json.dumps(memory, indent=2, ensure_ascii=False))

# CLI 輸出
print(f"[Memory Recorder] 第 {memory['live_rounds']} 輪完成 | 學習力={memory['learning_score']} | 標記：{', '.join(memory['bad_behavior_tag'])}")
