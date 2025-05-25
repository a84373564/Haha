import json
import random
from datetime import datetime
from pathlib import Path

# 路徑設定
king_path = Path("~/Killcore/modules/king.json").expanduser()
perf_path = Path("~/Killcore/king_performance.json").expanduser()
mem_path = Path("~/Killcore/king_memory.json").expanduser()
market_path = Path("~/Killcore/market_status.json").expanduser()
eval_path = Path("~/Killcore/king_self_evaluation.json").expanduser()

# 載入資料
king = json.loads(king_path.read_text())
perf = json.loads(perf_path.read_text())
memory = json.loads(mem_path.read_text()) if mem_path.exists() else {}
market = json.loads(market_path.read_text()) if market_path.exists() else {}
evaluation = json.loads(eval_path.read_text()) if eval_path.exists() else {}

# 預設值補全
memory.setdefault("evolution_trace", [])
memory.setdefault("live_rounds", 0)
memory.setdefault("learning_score", 0)
memory.setdefault("style_history", [])
memory.setdefault("drift_history", [])

# 提升進化代數
king["generation"] += 1
intent_summary = []
style_change = None

# 市況判斷（trend + volatility）
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

# 根據市況改變風格
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

# 自評進化策略：從模組 10 讀入 JSON 結果
grade = evaluation.get("evolution_grade", "")
trend_score = evaluation.get("trend_score", 0)

if grade.startswith("S+"):
    intent_summary.append("自評結果：實戰等級，凍結參數")
    king["evolution_intent"] = intent_summary
    king_path.write_text(json.dumps(king, indent=2, ensure_ascii=False))
    print("[Evolution Engine] S+ 評級 → 凍結參數不進化")
    exit(0)

elif grade.startswith("A"):
    king["parameters"]["tp_pct"] *= 1.05
    king["parameters"]["sl_pct"] *= 0.97
    intent_summary.append("自評 A 級 → 微幅強化 TP，縮小 SL")

elif grade.startswith("B"):
    king["parameters"]["tp_pct"] *= random.uniform(0.9, 1.1)
    king["parameters"]["sl_pct"] *= random.uniform(0.9, 1.1)
    king["risk_tolerance"] = min(max(king.get("risk_tolerance", 0.5) + random.uniform(-0.1, 0.1), 0.1), 1.0)
    intent_summary.append("自評 B 級 → 中度突變進化")

elif grade.startswith("C"):
    king["parameters"]["tp_pct"] = random.uniform(3, 8)
    king["parameters"]["sl_pct"] = random.uniform(1, 4)
    king["risk_tolerance"] = random.uniform(0.3, 0.7)
    style = random.choice(["balanced", "defensive", "explosive"])
    intent_summary.append("自評 C 級 → 重設策略與風格")

# 偵測風格變化
if king.get("style_profile") != style:
    style_change = f"{king['style_profile']} → {style}"
king["style_profile"] = style

# 記錄意圖與進化摘要
king["evolution_intent"] = intent_summary
evo_trace = {
    "generation": king["generation"],
    "ts": datetime.now().isoformat(),
    "intent": intent_summary,
    "style_profile": style,
    "grade": grade,
    "score": trend_score
}
memory["evolution_trace"].append(evo_trace)

# 寫入結果
king_path.write_text(json.dumps(king, indent=2, ensure_ascii=False))
mem_path.write_text(json.dumps(memory, indent=2, ensure_ascii=False))
print(f"[Evolution Engine] 第 {king['generation']} 代進化完成｜評級={grade}｜風格={style}")
