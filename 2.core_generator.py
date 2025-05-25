import json
import random
import hashlib
import time
from pathlib import Path
from datetime import datetime

# 目錄與檔案路徑
module_dir = Path("~/Killcore/modules").expanduser()
module_dir.mkdir(parents=True, exist_ok=True)
memory_file = Path("~/Killcore/symbol_memory.json").expanduser()

# 檢查幣種來源
if not memory_file.exists():
    raise FileNotFoundError("請先執行 symbol_selector.py")
memory = json.loads(memory_file.read_text())
selected_symbol = max(memory.items(), key=lambda x: x[1]["uses"])[0]

# 預設池
strategy_type = "MA_Crossover"
style_pool = ["defensive", "explosive", "balanced", "scalper"]
theme_pool = ["trend_following", "breakout", "mean_revert"]
emotions = ["greedy", "fearful", "hesitant", "balanced", "aggressive"]
indicators = ["MA", "RSI", "Volume", "MACD", "PriceAction"]

# 隨機風格參數
style = random.choice(style_pool)
if style == "defensive":
    ma_fast, ma_slow, sl, tp = 20, 60, 2, 4
elif style == "explosive":
    ma_fast, ma_slow, sl, tp = 8, 21, 4, 10
elif style == "scalper":
    ma_fast, ma_slow, sl, tp = 5, 13, 1.5, 2.5
else:
    ma_fast, ma_slow, sl, tp = 15, 45, 3, 6

parameters = {
    "ma_fast": ma_fast,
    "ma_slow": ma_slow,
    "sl_pct": sl,
    "tp_pct": tp
}

# 決策權重地圖
selected_indicators = random.sample(indicators, 3)
weights = [random.uniform(0.2, 0.5) for _ in range(3)]
s = sum(weights)
decision_map = {k: round(w / s, 2) for k, w in zip(selected_indicators, weights)}

# 核心辨識碼
now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
genetic_id = hashlib.md5((selected_symbol + now).encode()).hexdigest()[:12]
creation_id = f"{selected_symbol}_{now}"
training_trace_id = f"trace_{random.randint(100000,999999)}"

# 模組主體
module = {
    "id": "king",
    "symbol": selected_symbol,
    "strategy_type": strategy_type,
    "parameters": parameters,
    "capital": 70.51,
    "generation": 0,
    "style_profile": style,
    "strategy_theme": random.choice(theme_pool),
    "risk_tolerance": round(random.uniform(0.05, 0.2), 2),
    "max_live_rounds": 10,
    "init_bias_score": round(random.uniform(-1.0, 1.0), 2),
    "temperature_level": round(random.uniform(0.3, 0.9), 2),
    "genetic_id": genetic_id,
    "creation_id": creation_id,
    "created_by": "core_generator_v1",
    "human_note": "初代 king 模組。具備人格、風格、決策邏輯與風險偏好。",
    "decision_weighting_map": decision_map,
    "emotional_tendency": random.choice(emotions),
    "training_trace_id": training_trace_id,
    "version_stamp": "v1_full_final",
    "is_divine": False
}

# 儲存模組
with open(module_dir / "king.json", "w") as f:
    json.dump(module, f, indent=2)

print(f"[已產生模組] → {module_dir}/king.json")
print(json.dumps(module, indent=2))
