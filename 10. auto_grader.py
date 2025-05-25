import json
from pathlib import Path

# 路徑
mem_path = Path("~/Killcore/king_memory.json").expanduser()
perf_path = Path("~/Killcore/king_performance.json").expanduser()

# 載入資料
memory = json.loads(mem_path.read_text())
perf = json.loads(perf_path.read_text()) if perf_path.exists() else {}

# 評級變數
score = 0
reasons = []

# 判斷 1：學習力
learning_score = memory.get("learning_score", 0)
if learning_score >= 4:
    score += 1
    reasons.append("學習力穩定（≥4/5 輪正報酬）")
else:
    reasons.append("學習力尚未穩定")

# 判斷 2：報酬趨勢
returns = [r.get("return_pct", 0) for r in memory.get("history", [])[-5:]]
if all(r > 0 for r in returns[-3:]):
    score += 1
    reasons.append("最近三輪皆為正報酬")
else:
    reasons.append("尚未形成連續報酬曲線")

# 判斷 3：風格穩定性
styles = [r.get("style") for r in memory.get("history", [])[-5:] if r.get("style")]
if len(set(styles)) <= 2 and len(styles) >= 3:
    score += 1
    reasons.append("風格穩定（5 輪內無明顯漂移）")
else:
    reasons.append("風格尚未固定")

# 判斷 4：情緒穩定性（透過 bias / emotional 記錄）
emotions = [r.get("score_snapshot", {}).get("emotion") for r in memory.get("history", [])[-5:] if r.get("score_snapshot")]
if emotions.count(emotions[-1]) >= 3:
    score += 1
    reasons.append("情緒傾向穩定")
else:
    reasons.append("情緒仍在波動")

# 判斷 5：封印因子
seals = [k for k, v in memory.get("memory_flags", {}).items() if v == "封印候選"]
if not seals:
    score += 1
    reasons.append("無封印因子")
else:
    reasons.append(f"存在封印因子：{', '.join(seals)}")

# 判斷 6：爆發能力
explosions = [r.get("return_pct", 0) for r in memory.get("history", []) if r.get("return_pct", 0) >= 8]
if explosions:
    score += 1
    reasons.append(f"具備爆發輪（共 {len(explosions)} 次 ≥ +8%）")
else:
    reasons.append("尚無爆發性表現")

# 判斷 7：回撤與風控
drawdowns = [r.get("drawdown", 0) for r in memory.get("history", [])[-5:]]
if max(drawdowns, default=0) <= 4.5:
    score += 1
    reasons.append("回撤控制良好（近 5 輪皆 ≤ 4.5%）")
else:
    reasons.append("近期有高風險回撤")

# 評級總結
stars = "★" * score + "☆" * (7 - score)

# 輸出報告
print("\n[Auto Grader] 模組進化成熟度分析")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"評級：{stars}（{score} / 7）")
for r in reasons:
    print(" -", r)

# 實戰建議
if score >= 6:
    print("\n[建議] 模組已具備實盤實戰資格，可考慮進入實單測試")
elif score >= 4:
    print("\n[建議] 模組具備潛力，可進入沙盒或小額驗證")
else:
    print("\n[建議] 模組仍在成長階段，建議持續進化與觀察")
