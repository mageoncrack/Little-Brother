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

# --- Ollama CLI call ---
def run_model(model_name, prompt, file_path=None):
    instructions = load_behavior(model_name)
    full_prompt = instructions + prompt
    cmd = ["ollama", "run", model_name, "--prompt", full_prompt]
    if file_path:
        cmd += ["--file", str(file_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stderr:
        print(f"[Ollama error] {result.stderr.strip()}")
    return result.stdout.strip()

# --- Generate session name ---
def generate_session_name(initial_messages, personality_model):
    context_text = "\n".join([f"{m['role']}: {m['content']}" for m in initial_messages])
    prompt = (
        f"Based on the following conversation, generate a short descriptive title "
        f"(3-5 words) without punctuation:\n{context_text}"
    )
    raw_title = run_model(personality_model, prompt)
    title = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_title)
    return title[:50]

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

# --- Load session ---
def load_session(file_path):
    with open(file_path) as f:
        return json.load(f)

# --- Optional File Explorer ---
def open_file_explorer():
    sessions_path = sessions_dir.resolve()
    if os.name == "nt":
        subprocess.run(f'explorer "{sessions_path}"', shell=True)
    elif os.name == "posix":
        if sys.platform == "darwin":
            subprocess.run(["open", str(sessions_path)])
        else:
            subprocess.run(["xdg-open", str(sessions_path)])

# --- Choose old session ---
def choose_session():
    choice = input("Load session list in File Explorer? (y/n): ").lower()
    if choice == "y":
        open_file_explorer()
    session_file = input("Write session name to load: ")
    session_path = sessions_dir / f"{session_file}.json"
    if not session_path.exists():
        print("Session not found! Try again.")
        return choose_session()
    return session_path

# --- Route to helper models and aggregate for personality ---
def route_to_helpers(user_input):
    helper_models = {
        "coding": routing.get("coding"),
        "reasoning": routing.get("reasoning"),
        "visual": routing.get("visual")
    }
    outputs = {}
    for name, model in helper_models.items():
        if name == "visual" and any(word in user_input.lower() for word in ["image", "photo", "video", "picture"]):
            file_path = input("Enter path to image/video: ").strip()
            outputs[name] = run_model(model, user_input, file_path=file_path)
        else:
            outputs[name] = run_model(model, user_input)
    return outputs

# --- Personality model handles all output ---
def lilbro_response(session_file, user_input):
    # Load session
    with open(session_file) as f:
        session_data = json.load(f)

    # Current context
    session_messages = session_data["messages"] + [{"role": "user", "content": user_input}]

    # Convert messages to text
    prompt_text = ""
    for msg in session_messages:
        prompt_text += f"{msg['role'].capitalize()}: {msg['content']}\n"

    # Collect helper outputs
    helper_outputs = route_to_helpers(prompt_text)
    helpers_text = "\n".join([f"[{k} model output]: {v}" for k, v in helper_outputs.items()])

    # Final prompt to personality model
    personality_prompt = f"{prompt_text}\n{helpers_text}\nRespond to the user as yourself."

    # Call personality model
    response = run_model(routing["personality"], personality_prompt)
    return response

# --- Main CLI ---
if __name__ == "__main__":
    print("LilBro CLI is ready.\n")
    choice = input("1: Start new session\n2: Load old session\nChoose (1/2): ").strip()

    if choice == "1":
        initial_msg = input("First message to LilBro: ")
        initial_messages = [{"role": "user", "content": initial_msg}]
        session_name = generate_session_name(initial_messages, routing["personality"])
        session_file = sessions_dir / f"{session_name}.json"
        for msg in initial_messages:
            save_message(session_file, msg["role"], msg["content"])
        print(f"Session created: {session_name}")

    else:
        session_file = choose_session()
        session_data = load_session(session_file)
        print(f"Loaded session: {session_file.stem}")

    print("\nType 'exit' to quit.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        response = lilbro_response(session_file, user_input)
        print(f"LilBro: {response}")

        save_message(session_file, "user", user_input)
        save_message(session_file, "assistant", response)
