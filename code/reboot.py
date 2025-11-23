import subprocess, time, sys, os

time.sleep(1)

python_cmd = sys.executable
script_path = os.path.join(os.path.dirname(__file__), "bot.py")
subprocess.Popen([python_cmd, script_path])
exit()