import json
from datetime import datetime
from typing import Dict
from src.core.config import LOG_FILE

def message(role: str, content: str) -> Dict[str, str]:
    return {"role": role, "content": content}

def save_chat_log(user_input: str, assistant_reply: str) -> None:
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_input,
        "assistant_message": assistant_reply,
    }
    try:
        if not LOG_FILE.exists():
            LOG_FILE.write_text(json.dumps([entry], indent=2), encoding="utf-8")
        else:
            data = json.loads(LOG_FILE.read_text(encoding="utf-8"))
            data.append(entry)
            LOG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        print("Logging error:", e)
