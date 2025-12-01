# Little-Brother CLI AI

## Overview
Little-Brother is a CLI AI assistant that acts like a mini ChatGPT:
- Multi-model routing (personality, coding, reasoning)
- Automatic session management
- AI-generated session names
- Persistent memory per session

## Setup
1. Install Python 3.10+ and add to PATH.
2. Clone this repo:
```powershell
git clone https://github.com/YourUsername/Little-Brother.git
cd Little-Brother
```
3. Install dependencies
```powershell
pip install -r requirements.txt
```
4. Install Ollama CLI
Download and install Ollama from https://ollama.com.
Make sure ollama --version works in your terminal:
```powershell
ollama --version
```
 5. Pull Models
 ```powershell
 python model_setup.py
 ```

 6. Run Little-Brother
 ```powershell 
 python littlebrother.py
```

## Adding or Changing Models
- Update config/routing.json with new models:

  {
    "personality": "llama3.1:8b",
    "coding": "qwen2.5-coder:7b",
    "reasoning": "deepseek-r1:7b"
  }

- Re-run python model_setup.py to ensure new models are installed.


## Notes
- Make sure Ollama CLI works in your terminal before running Little-Brother.
- All session files are persistent and can be loaded anytime.
- Python scripts handle everything except the initial Ollama CLI installation.
