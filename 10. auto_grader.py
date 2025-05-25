import json
from pathlib import Path
from datetime import datetime

king_path = Path("~/Killcore/modules/king.json").expanduser()
perf_path = Path("~/Killcore/king_performance.json").expanduser()
mem_path = Path("~/Killcore/king_memory.json").expanduser()

# 載入資料
king = json.loads(king_path.read_text())
perf = json.loads(perf_path.read_text())
memory = json.loads(mem_path.read_text())

history = memory.get("history", [])
trace = memory.get("evolution_trace", [])
fail_counts = memory.get("fail_indicators_count", {})

# 報酬趨勢統計
returns = [r.get("return_pct", 0) for r in history]
avg_return_start = sum(returns[:5]) / 5 if len(returns) >= 5 else 0
avg_return_recent = sum(returns[-5:]) / 5 if len(returns) >= 5 else 0
sharpe_values = [r.get("sharpe", 0) for r in history if "sharpe" in r]
avg_sharpe_start = sum(sharpe_values[:5]) / 5 if len(sharpe_values) >= 5 else 0
avg_sharpe_recent = sum(sharpe_values[-5:]) / 5 if len(sharpe_values) >= 5 else 0

# 意圖多樣性
intents = set()
for r in trace:
    intent = tuple(r.get("intent", []))
    if intent:
        intents.add(intent)

# 風格變異計算
style_profile_history = [r.get("style_profile") for r in trace if r.get("style_profile")]
style_variants = len(set(style_profile_history))

# 失敗類型統計
fail_total = sum(fail_counts.values())
top_fail = sorted(fail_counts.items(), key=lambda x: x[1], reverse=True)[:3]

# 空轉偵測
stagnant = False
if len(returns) >= 10:
    recent = returns[-5:]
    all_small = all(abs(r) < 1 for r in recent)
    same_intent = len(set(",".join(map(str, r.get("intent", []))) for r in trace[-5:])) == 1
    if all_small and same_intent:
        stagnant = True

# 報告輸出
print("\n[Auto Grader] 模組完整歷史進化診斷")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"代數：{king.get('generation')} ｜ 生存輪數：{memory.get('live_rounds', len(history))}")
print(f"報酬趨勢：{avg_return_start:+.2f}% → {avg_return_recent:+.2f}%")
print(f"Sharpe 指數：{avg_sharpe_start:.2f} → {avg_sharpe_recent:.2f}")
print(f"風格變化次數：{style_variants} ｜ 當前風格：{king.get('style_profile')}")
print(f"意圖多樣性：{len(intents)} 種 ｜ 失敗總數：{fail_total}")
print(f"Top 失敗原因：", ", ".join([f"{k}({v})" for k,v in top_fail]) or "無")

# 綜合評估
print("\n【綜合判斷】：", end="")
if stagnant:
    print("模組疑似進入空轉（報酬無進展、意圖重複）")
elif avg_return_recent > avg_return_start and avg_sharpe_recent > avg_sharpe_start:
    print("模組正在穩定成長，進化方向良好")
else:
    print("模組仍在調整階段，部分進化未達標")

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"評估時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
