import subprocess
import json
from pathlib import Path
import re
import os
import sys

# --- Paths ---
sessions_dir = Path("sessions")
sessions_dir.mkdir(exist_ok=True)

config_path = Path("config/routing.json")
behavior_dir = Path("behavior_instruct")

# --- Load routing config ---
with open(config_path) as f:
    routing = json.load(f)

# --- Load behavior instructions ---
def load_behavior(model_name):
    file_path = behavior_dir / f"{model_name.split(':')[0]}.txt"
    if file_path.exists():
        return file_path.read_text().strip() + "\n\n"
    return ""

# --- Run model via Ollama (FIXED: uses STDIN so it doesn't freeze) ---
def run_model(model_name, prompt):
    instructions = load_behavior(model_name)
    full_prompt = instructions + prompt

    process = subprocess.Popen(
        ["ollama", "run", model_name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",         # <--- FORCE UTF-8 on input/output
        errors="replace"          # <--- prevent crashes on weird chars
    )

    stdout, stderr = process.communicate(full_prompt)

    if stderr:
        print(f"[Ollama error] {stderr.strip()}")

    return stdout.strip()


# --- Generate session name ---
def generate_session_name(initial_messages, personality_model):
    context_text = "\n".join(
        [f"{m['role']}: {m['content']}" for m in initial_messages]
    )
    prompt = (
        "Generate a short descriptive title (3-5 words) without punctuation for this conversation:\n"
        + context_text
    )
    raw_title = run_model(personality_model, prompt)

    if not raw_title:
        return "session_default"

    title = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_title)
    return title[:50] if title else "session_default"

# --- Save messages ---
def save_message(session_file, role, content):
    if not session_file.exists():
        session_data = {"session_name": session_file.stem, "messages": []}
    else:
        with open(session_file) as f:
            session_data = json.load(f)

    session_data["messages"].append({"role": role, "content": content})

    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)

# --- Load session file ---
def load_session(file_path):
    with open(file_path) as f:
        return json.load(f)

# --- Open session picker ---
def choose_session():
    choice = input("Load session list in File Explorer? (y/n): ").lower()
    if choice == "y":
        sessions_path = sessions_dir.resolve()
        if os.name == "nt":
            subprocess.run(f'explorer "{sessions_path}"', shell=True)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(sessions_path)])
        else:
            subprocess.run(["xdg-open", str(sessions_path)])

    name = input("Write session name to load: ")
    path = sessions_dir / f"{name}.json"

    if not path.exists():
        print("Session not found! Try again.")
        return choose_session()

    return path

# --- Helper routing (coding + reasoning only, no visual) ---
def route_to_helpers(user_input):
    helper_models = {
        "coding": routing.get("coding"),
        "reasoning": routing.get("reasoning")
    }
    outputs = {}

    for name, model in helper_models.items():
        outputs[name] = run_model(model, user_input)

    return outputs

# --- Personality model handles final answer ---
def littlebrother_response(session_file, user_input):
    with open(session_file) as f:
        session_data = json.load(f)

    session_messages = session_data["messages"] + [{"role": "user", "content": user_input}]

    prompt_text = ""
    for msg in session_messages:
        prompt_text += f"{msg['role'].capitalize()}: {msg['content']}\n"

    helper_outputs = route_to_helpers(prompt_text)
    helper_text = "\n".join([f"[{k} model output]: {v}" for k, v in helper_outputs.items()])

    final_prompt = (
        f"{prompt_text}\n{helper_text}\n"
        f"Respond to the user as yourself."
    )

    response = run_model(routing["personality"], final_prompt)
    return response

# --- MAIN CLI ---
if __name__ == "__main__":
    print("Little-Brother CLI is ready.\n")
    choice = input("1: Start new session\n2: Load old session\nChoose (1/2): ").strip()

    if choice == "1":
        # no "First message" prompt anymore
        initial_msg = input("You: ")
        initial_messages = [{"role": "user", "content": initial_msg}]
        session_name = generate_session_name(initial_messages, routing["personality"])
        session_file = sessions_dir / f"{session_name}.json"

        for msg in initial_messages:
            save_message(session_file, msg["role"], msg["content"])

        print(f"\nNew session started with Little-Brother: {session_name}\n")

    else:
        session_file = choose_session()
        session_data = load_session(session_file)
        print(f"\nLoaded session: {session_file.stem}\n")

    while True:
        user_input = input("You: ")
        response = littlebrother_response(session_file, user_input)
        print(f"\nLittle-Brother: {response}\n")

        save_message(session_file, "user", user_input)
        save_message(session_file, "assistant", response)
