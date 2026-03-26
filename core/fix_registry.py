import hashlib
import json
import os
import re
import shutil
import traceback
import zipfile
from datetime import datetime
from typing import Any

from core.logger import SOLUTIONS_DIR, EXPORTS_DIR, get_logger

REGISTRY_PATH = os.path.join(SOLUTIONS_DIR, "fix_registry.json")
REGISTRY_VERSION = 1


def _normalize_message(msg: str) -> str:
    msg = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", msg)
    msg = re.sub(r"\d{4}-\d{2}-\d{2}", "DATE", msg)
    msg = re.sub(r"/[\w/.\-]+", "PATH", msg)
    msg = re.sub(r"\d+", "N", msg)
    return msg.strip()


def _extract_top_frames(exc_tb: Any, count: int = 3) -> list[str]:
    frames: list[str] = []
    if exc_tb is None:
        return frames
    entries = traceback.extract_tb(exc_tb)
    for entry in entries[-count:]:
        basename = os.path.basename(entry.filename)
        frames.append(f"{basename}:{entry.name}:{entry.lineno}")
    return frames


def compute_fingerprint(
    exc_type: type | None = None,
    exc_value: BaseException | None = None,
    exc_tb: Any = None,
) -> str:
    parts: list[str] = []
    if exc_type:
        parts.append(exc_type.__name__)
    else:
        parts.append("UnknownError")
    if exc_value:
        parts.append(_normalize_message(str(exc_value)))
    else:
        parts.append("")
    parts.extend(_extract_top_frames(exc_tb, 3))
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _load_registry() -> dict[str, Any]:
    if not os.path.isfile(REGISTRY_PATH):
        return {"version": REGISTRY_VERSION, "fixes": {}}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "fixes" not in data:
        return {"version": REGISTRY_VERSION, "fixes": {}}
    return data


def _save_registry(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def lookup_fix(fingerprint: str) -> dict[str, Any] | None:
    registry = _load_registry()
    return registry["fixes"].get(fingerprint)


def save_fix(
    fingerprint: str,
    case_folder: str,
    title: str,
    root_cause: str,
    fix_steps: str,
    verification: str,
    auto_fix_script: str = "",
) -> None:
    registry = _load_registry()
    entry: dict[str, Any] = {
        "fingerprint": fingerprint,
        "title": title,
        "root_cause": root_cause,
        "fix_steps": fix_steps,
        "verification": verification,
        "case_folder": case_folder,
        "created": datetime.now().isoformat(),
    }
    if auto_fix_script:
        entry["auto_fix_script"] = auto_fix_script
    registry["fixes"][fingerprint] = entry
    _save_registry(registry)
    get_logger("fix_registry").info(f"Fix saved: {fingerprint} — {title}")


def register_case_fingerprint(fingerprint: str, case_folder: str) -> None:
    registry = _load_registry()
    existing = registry["fixes"].get(fingerprint)
    if existing is None:
        registry["fixes"][fingerprint] = {
            "fingerprint": fingerprint,
            "title": "",
            "root_cause": "",
            "fix_steps": "",
            "verification": "",
            "case_folder": case_folder,
            "created": datetime.now().isoformat(),
            "status": "unfixed",
        }
        _save_registry(registry)


def export_fix_pack() -> str:
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    zip_path = os.path.join(EXPORTS_DIR, f"fix_pack_{ts}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isfile(REGISTRY_PATH):
            zf.write(REGISTRY_PATH, "fix_registry.json")

        registry = _load_registry()
        for fp, entry in registry["fixes"].items():
            script = entry.get("auto_fix_script", "")
            if script and os.path.isfile(script):
                zf.write(script, f"scripts/{os.path.basename(script)}")

    get_logger("fix_registry").info(f"Fix pack exported: {zip_path}")
    return zip_path


def import_fix_pack(zip_path: str) -> int:
    if not os.path.isfile(zip_path):
        raise FileNotFoundError(f"Fix pack not found: {zip_path}")

    imported_count = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        if "fix_registry.json" not in zf.namelist():
            raise ValueError("Invalid fix pack: no fix_registry.json found")

        incoming_data = json.loads(zf.read("fix_registry.json").decode("utf-8"))
        incoming_fixes = incoming_data.get("fixes", {})

        registry = _load_registry()
        for fp, entry in incoming_fixes.items():
            if fp not in registry["fixes"]:
                registry["fixes"][fp] = entry
                imported_count += 1
            else:
                existing = registry["fixes"][fp]
                if not existing.get("title") and entry.get("title"):
                    registry["fixes"][fp] = entry
                    imported_count += 1

        script_names = [n for n in zf.namelist() if n.startswith("scripts/")]
        if script_names:
            scripts_dir = os.path.join(SOLUTIONS_DIR, "imported_scripts")
            os.makedirs(scripts_dir, exist_ok=True)
            for name in script_names:
                target = os.path.join(scripts_dir, os.path.basename(name))
                with open(target, "wb") as f:
                    f.write(zf.read(name))

        _save_registry(registry)

    get_logger("fix_registry").info(
        f"Fix pack imported: {zip_path} ({imported_count} new/updated fixes)"
    )
    return imported_count
