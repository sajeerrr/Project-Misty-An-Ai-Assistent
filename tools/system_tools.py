import subprocess
from config.settings import DANGEROUS_COMMANDS


def run_command(cmd):
    if any(d in cmd.lower() for d in DANGEROUS_COMMANDS):
        return "❌ Blocked dangerous command"

    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True
        )
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)


def open_app(name):
    return run_command(f"start {name}")