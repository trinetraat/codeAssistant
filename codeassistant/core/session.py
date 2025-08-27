import json, datetime
from pathlib import Path
from typing import Dict, List, Optional
from .config import SESS_DIR, OUT_DIR

def session_path(project_id: str) -> Path:
    return SESS_DIR / f"{project_id}.json"

def spec_path(project_id: str) -> Path:
    return SESS_DIR / f"{project_id}_spec.md"

def load_session(project_id: str) -> Dict:
    p = session_path(project_id)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"project_id": project_id, "created_at": datetime.datetime.utcnow().isoformat(),
            "model": None, "billing": {"total_usd": 0.0, "turns": []}, "turns": []}

def save_session(project: Dict) -> None:
    session_path(project["project_id"]).write_text(json.dumps(project, indent=2), encoding="utf-8")

def add_turn(project: Dict, role: str, content: str, usage: Optional[Dict]=None) -> None:
    turn = {"role": role, "content": content, "ts": datetime.datetime.utcnow().isoformat()}
    if usage: turn["usage"] = usage
    project["turns"].append(turn)

def outputs_dir() -> Path:
    return OUT_DIR