import subprocess
import sys
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# --- SETTINGS ---
RESTART_ON_CRASH = False  # Set to True if you want auto-restart on crashes
CRASH_WEBHOOK_URL = os.getenv("CRASH_WEBHOOK_URL") 
USER_ID = "859371145076932619" 

def send_alert(message):
    if not CRASH_WEBHOOK_URL:
        return
    data = {"content": message, "username": "System Monitor"}
    try:
        requests.post(CRASH_WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"Failed to send alert: {e}")

def run_bot():
    # DYNAMICALLY FIND PATH
    # This fixes the "No such file" error by finding main.py relative to THIS file (launch.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "main.py")
    
    if not os.path.exists(script_path):
        print(f"❌ CRITICAL ERROR: Could not find file at: {script_path}")
        return -1 # Custom error code for missing file

    print(f"🚀 Launching: {script_path}")
    
    process = subprocess.Popen([sys.executable, script_path])
    
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return 0
        
    return process.returncode

def main():
    print("--- SYSTEM SUPERVISOR STARTED ---")
    
    while True:
        exit_code = run_bot()
        
        # Missing File Check
        if exit_code == -1:
            print("Terminating supervisor to prevent infinite loop.")
            break

        # Code 0: Clean Exit (User ran /kill or Ctrl+C)
        if exit_code == 0:
            print("✅ Bot shut down normally.")
            break
            
        # Code 2: Reboot Request (User ran /reboot)
        elif exit_code == 2:
            print("🔄 Reboot requested. Restarting...")
            time.sleep(1)
            continue 
            
        # Code 1: Crash / Error
        else:
            print(f"❌ Bot Crashed (Exit Code: {exit_code})")
            msg = f"<@{USER_ID}> 🚨 **Bot Crashed** (Exit Code {exit_code})"
            send_alert(msg)
            
            if RESTART_ON_CRASH:
                print("⚠️ Restarting in 5 seconds...")
                time.sleep(5)
                continue
            else:
                print("⚠️ Auto-restart is DISABLED. Supervisor exiting.")
                break

if __name__ == "__main__":
    main()