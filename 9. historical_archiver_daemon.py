import subprocess
import time
import os
from pathlib import Path

LOCK_FILE = Path("/tmp/killcore_archiver.lock")

def is_already_running():
    if LOCK_FILE.exists():
        print("[Daemon] 已有執行實例在運行中，略過啟動")
        return True
    else:
        LOCK_FILE.write_text(str(os.getpid()))
        return False

def clear_lock():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()

def run_one_round():
    result = subprocess.run(["python3", str(Path("~/Killcore/historical_archiver.py").expanduser())])
    return result.returncode == 0

if __name__ == "__main__":
    try:
        if is_already_running():
            exit(0)

        print("[Daemon] 背景掛機啟動，每 10 秒執行一輪 Killcore 模組")
        while True:
            success = run_one_round()
            if success:
                print("[Daemon] 本輪執行完成，等待 10 秒...")
            else:
                print("[Daemon] 執行異常，等待 10 秒重試...")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n[Daemon] 偵測到中斷，準備離開...")
    finally:
        clear_lock()
        print("[Daemon] 掛機程序結束，已清除鎖定")
