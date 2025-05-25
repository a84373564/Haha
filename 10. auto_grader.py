import json
from pathlib import Path
from statistics import mean, stdev

mem_path = Path("~/Killcore/king_memory.json").expanduser()
output_path = Path("~/Killcore/king_self_evaluation.json").expanduser()

if not mem_path.exists():
    raise FileNotFoundError("找不到 king_memory.json")

memory = json.loads(mem_path.read_text())
history = memory.get("history", [])[-20:]  # 只分析最近 20 輪
evo_trace = memory.get("evolution_trace", [])[-5:]
fail_stats = memory.get("fail_indicators_count", {})

# --- 趨勢評估 ---
returns = [r.get("return_pct", 0) for r in history]
drawdowns = [r.get("drawdown", 100) for r in history]
win_rates = [r.get("win_rate", 0) for r in history]

def trend_direction(data):
    return "上升" if len(data) >= 2 and data[-1] > data[0] else "下降"

def stability_score(data):
    return round(stdev(data), 2) if len(data) >= 2 else 0

trend_report = {
    "return_trend": trend_direction(returns),
    "drawdown_trend": trend_direction(drawdowns[::-1]),
    "winrate_trend": trend_direction(win_rates),
    "return_std": stability_score(returns),
    "drawdown_avg": round(mean(drawdowns), 2) if drawdowns else 100,
    "learning_score": memory.get("learning_score", 0),
    "fail_count": sum(fail_stats.values())
}

# --- 評分與標籤 ---
score = 0
if trend_report["return_trend"] == "上升": score += 2
if trend_report["drawdown_trend"] == "下降": score += 2
if trend_report["return_std"] < 3: score += 1
if trend_report["learning_score"] >= 4: score += 1
if trend_report["fail_count"] < 10: score += 1

if score >= 6:
    level = "S+（已達實戰）"
    advice = "建議保守進化或微調風格以穩定實戰績效"
elif score >= 4:
    level = "A（穩定進化中）"
    advice = "維持風格主軸，可調整進場與TP/SL參數"
elif score >= 2:
    level = "B（波動偏高）"
    advice = "需觀察，考慮強化風險管理或改變策略"
else:
    level = "C（退化或失控）"
    advice = "建議重置進化方向，並記錄錯誤模式"

# --- 產出 JSON 給模組 3 使用 ---
result = {
    "evolution_grade": level,
    "trend_score": score,
    "trend_report": trend_report,
    "evolution_advice": advice,
    "status_flag": "ok"
}
output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

# CLI 顯示給人類參考
print("— 模組 10：自我進化分析報告 —")
print(f"狀態等級：{level}")
print(f"趨勢分數：{score} 分")
print("報酬趨勢：", trend_report["return_trend"])
print("回撤趨勢：", trend_report["drawdown_trend"])
print("勝率趨勢：", trend_report["winrate_trend"])
print("報酬波動度：", trend_report["return_std"])
print("學習力：", trend_report["learning_score"], "/ 5")
print("失敗總數：", trend_report["fail_count"])
print("建議行動：", advice)
