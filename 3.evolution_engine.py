import json
import random
from pathlib import Path

# 檔案路徑
module_path = Path("~/Killcore/modules/king.json").expanduser()
performance_path = Path("~/Killcore/king_performance.json").expanduser()
memory_path = Path("~/Killcore/king_memory.json").expanduser()
market_status_path = Path("~/Killcore/market_status.json").expanduser()

# 載入 king 模組
if not module_path.exists():
    raise FileNotFoundError("找不到 king 模組")
king = json.loads(module_path.read_text())

# 載入績效資料
if not performance_path.exists():
    raise FileNotFoundError("缺少績效資料 king_performance.json")
perf = json.loads(performance_path.read_text())

# 防錯強化：記憶載入
if not memory_path.exists():
    raise FileNotFoundError("缺少記憶體資料 king_memory.json")
try:
    memory = json.loads(memory_path.read_text())
except json.JSONDecodeError as e:
    print("[錯誤] king_memory.json 格式異常，無法進化")
    raise

# 防錯強化：市況載入
if not market_status_path.exists():
    raise FileNotFoundError("缺少市況資料 market_status.json")
try:
    market = json.loads(market_status_path.read_text())
except json.JSONDecodeError as e:
    print("[錯誤] market_status.json 格式異常，無法進化")
    raise

# 進化紀錄
king["generation"] += 1
evolution_log = []

# 評估條件
bad = perf["return_pct"] < 0 or perf["drawdown"] > king["risk_tolerance"]
good = perf["return_pct"] > 0 and perf["win_rate"] > 60

# 工具
def mutate_param(val, pct=0.1, minv=1, maxv=999):
    return max(minv, min(int(val * (1 + random.uniform(-pct, pct))), maxv))

def clip_float(val, pct=0.2, minv=0.1, maxv=10):
    delta = val * pct
    return round(min(maxv, max(minv, val + random.uniform(-delta, delta))), 2)

# 進化策略
if bad:
    king["parameters"]["sl_pct"] = clip_float(king["parameters"]["sl_pct"], 0.3, 0.5, 10)
    king["parameters"]["tp_pct"] = clip_float(king["parameters"]["tp_pct"], 0.3, 0.5, 15)
    king["init_bias_score"] = round(king["init_bias_score"] - 0.1, 2)
    king["temperature_level"] = round(min(king["temperature_level"] + 0.1, 1.0), 2)
    evolution_log.append("虧損 → 調整 SL/TP 與偏誤")

if good:
    king["parameters"]["ma_fast"] = mutate_param(king["parameters"]["ma_fast"], 0.05, 2)
    king["parameters"]["ma_slow"] = mutate_param(king["parameters"]["ma_slow"], 0.05, 5)
    king["init_bias_score"] = round(king["init_bias_score"] + 0.05, 2)
    evolution_log.append("獲利 → 微調 MA 與偏誤")

# 懲罰失敗指標
for i in memory.get("fail_indicators", []):
    if i in king["decision_weighting_map"]:
        king["decision_weighting_map"][i] = round(king["decision_weighting_map"][i] * 0.9, 2)
        evolution_log.append(f"降低失敗指標權重：{i}")

# 市況波動處理
if market.get("btc_volatility", 0) > 5:
    king["risk_tolerance"] = round(min(0.25, king["risk_tolerance"] + 0.02), 2)
    evolution_log.append("市況波動大 → 提高風險容忍")

# 更新進化意圖
king["evolution_intent"] = evolution_log

# 儲存新版 king
module_path.write_text(json.dumps(king, indent=2))
print(f"[OK] king 已進化至第 {king['generation']} 代。")
for log in evolution_log:
    print(" -", log)
