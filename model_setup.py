import subprocess
import json
from pathlib import Path

# --- Paths ---
config_path = Path("config/routing.json")

# --- Load routing config ---
with open(config_path) as f:
    routing = json.load(f)

# --- Check if model exists ---
def model_exists(model_name):
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True, text=True
    )
    return model_name in result.stdout

# --- Pull model ---
def pull_model(model_name):
    if model_exists(model_name):
        print(f"[INFO] Model already installed: {model_name}")
        return
    print(f"[INFO] Pulling model: {model_name} ...")
    result = subprocess.run(
        ["ollama", "pull", model_name],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"[SUCCESS] Model pulled: {model_name}")
    else:
        print(f"[ERROR] Failed to pull {model_name}:\n{result.stderr}")

# --- Main ---
if __name__ == "__main__":
    print("[INFO] Setting up all models from routing.json...\n")
    for key, model in routing.items():
        if model:
            pull_model(model)
    print("\n✅ All models ready!")
