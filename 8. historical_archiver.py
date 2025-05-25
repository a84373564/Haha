import subprocess
import time
import shutil
import os
from pathlib import Path
from datetime import datetime

# 執行模組清單（依照順序）
modules = [
    "symbol_selector.py",
    "core_generator.py",
    "live_simulator.py",
    "memory_recorder.py",  # 第一次記憶
    "evolution_engine.py",
    "memory_recorder.py",  # 第二次進化補記憶
    "insight_reporter.py",
    "memory_regulator.py"
]

start = time.time()
print("\n[Archiver] 啟動連貫執行器...\n")

killcore_path = Path("~/Killcore").expanduser()
log = []

# 依順序執行模組
for module in modules:
    module_path = killcore_path / module
    if not module_path.exists():
        print(f"[略過] 找不到模組：{module}")
        continue
    print(f"[執行] {module} ...")
    t0 = time.time()
    result = subprocess.run(["python3", str(module_path)], capture_output=True, text=True)
    t1 = time.time()
    print(result.stdout)
    if result.stderr:
        print(f"[錯誤] {module} 發生錯誤：\n{result.stderr}")
    log.append((module, round(t1 - t0, 2)))

# 建立封存資料夾
archives_path = killcore_path / "archives"
archives_path.mkdir(exist_ok=True)

# 編號 round
existing = [p for p in archives_path.iterdir() if p.is_dir() and p.name.startswith("round_")]
round_num = len(existing) + 1
round_dir = archives_path / f"round_{round_num:04d}"
round_dir.mkdir()

# 要封存的檔案
files_to_archive = ["modules/king.json", "king_performance.json", "king_memory.json"]
for f in files_to_archive:
    src = killcore_path / f
    if src.exists():
        shutil.copy(src, round_dir / Path(f).name)

# 完成報告
print("\n[Archiver] 本輪執行完成")
print(f"封存位置：{round_dir}")
print(f"執行耗時：{round(time.time() - start, 2)} 秒")
for mod, secs in log:
    print(f" - {mod:<24} 用時 {secs} 秒")
