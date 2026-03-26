import logging
import os
import sys
import platform
import traceback
import json
import zipfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(_PROJECT_ROOT, "logs")
CRASHES_DIR = os.path.join(LOGS_DIR, "crashes")
SOLUTIONS_DIR = os.path.join(_PROJECT_ROOT, "solutions_and_learning")
EXPORTS_DIR = os.path.join(_PROJECT_ROOT, "exports")

LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)-20s %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logger: logging.Logger | None = None


def setup_logging() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(CRASHES_DIR, exist_ok=True)

    logger = logging.getLogger("kds_lpe")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    logger.addHandler(console_handler)

    log_file = os.path.join(LOGS_DIR, "app.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    logger.addHandler(file_handler)

    _logger = logger
    logger.info("Logging initialized")
    return logger


def get_logger(name: str = "") -> logging.Logger:
    if _logger is None:
        setup_logging()
    if name:
        return logging.getLogger(f"kds_lpe.{name}")
    return logging.getLogger("kds_lpe")


def _get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def _get_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _build_system_info() -> dict[str, str]:
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "platform": platform.platform(),
        "python_version": sys.version,
        "machine": platform.machine(),
    }


def write_crash_report(
    exc_type: type | None = None,
    exc_value: BaseException | None = None,
    exc_tb: Any = None,
    action: str = "",
    app_state: dict[str, Any] | None = None,
) -> tuple[str, str]:
    os.makedirs(CRASHES_DIR, exist_ok=True)
    ts = _get_timestamp()
    filename = f"crash_{ts}.txt"
    path = os.path.join(CRASHES_DIR, filename)

    lines: list[str] = []
    lines.append(f"Crash Report — {ts}")
    lines.append("=" * 60)
    lines.append("")

    lines.append("SYSTEM INFO")
    lines.append("-" * 40)
    for k, v in _build_system_info().items():
        lines.append(f"  {k}: {v}")
    lines.append("")

    if action:
        lines.append(f"ACTION: {action}")
        lines.append("")

    lines.append("STACK TRACE")
    lines.append("-" * 40)
    if exc_type and exc_value and exc_tb:
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        lines.extend(line.rstrip() for line in tb_lines)
    elif exc_value:
        lines.append(str(exc_value))
    else:
        lines.append("(no exception info)")
    lines.append("")

    if app_state:
        lines.append("APP STATE")
        lines.append("-" * 40)
        for k, v in app_state.items():
            lines.append(f"  {k}: {v}")
    lines.append("")

    from core.fix_registry import compute_fingerprint
    fingerprint = compute_fingerprint(exc_type, exc_value, exc_tb)
    lines.append(f"FINGERPRINT: {fingerprint}")
    lines.append("")

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    get_logger("crash").error(f"Crash report written: {path} [fp={fingerprint}]")
    return path, fingerprint


def write_solution_folder(
    exc_type: type | None = None,
    exc_value: BaseException | None = None,
    exc_tb: Any = None,
    action: str = "",
    app_state: dict[str, Any] | None = None,
    analysis_results: dict[str, Any] | None = None,
    project_dict: dict[str, Any] | None = None,
    selection_info: dict[str, Any] | None = None,
    ui_mode_info: dict[str, Any] | None = None,
) -> str:
    os.makedirs(SOLUTIONS_DIR, exist_ok=True)
    ts = _get_timestamp()
    folder = os.path.join(SOLUTIONS_DIR, f"issue_{ts}")
    os.makedirs(folder, exist_ok=True)

    crash_lines: list[str] = []
    crash_lines.append(f"Error Report — {ts}")
    crash_lines.append("=" * 60)
    crash_lines.append("")
    crash_lines.append("SYSTEM INFO")
    crash_lines.append("-" * 40)
    for k, v in _build_system_info().items():
        crash_lines.append(f"  {k}: {v}")
    crash_lines.append("")
    if action:
        crash_lines.append(f"ACTION: {action}")
        crash_lines.append("")
    crash_lines.append("STACK TRACE")
    crash_lines.append("-" * 40)
    if exc_type and exc_value and exc_tb:
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
        crash_lines.extend(line.rstrip() for line in tb_lines)
    elif exc_value:
        crash_lines.append(str(exc_value))
    else:
        crash_lines.append("(no exception info)")
    crash_lines.append("")
    if app_state:
        crash_lines.append("APP STATE")
        crash_lines.append("-" * 40)
        for k, v in app_state.items():
            crash_lines.append(f"  {k}: {v}")

    with open(os.path.join(folder, "error_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(crash_lines))

    repro = [
        f"# Reproduction Steps — {ts}",
        "",
        f"## Action attempted: {action or '(unknown)'}",
        "",
        "## Steps to reproduce:",
        "1. ",
        "2. ",
        "3. ",
        "",
        "## Expected behavior:",
        "",
        "## Actual behavior:",
        "",
        "## Additional notes:",
        "",
    ]
    with open(os.path.join(folder, "repro_steps.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(repro))

    context: dict[str, Any] = {}
    if project_dict:
        context["project"] = project_dict
    if selection_info:
        context["selection"] = selection_info
    if ui_mode_info:
        context["ui_mode"] = ui_mode_info
    if analysis_results:
        context["analysis_results"] = analysis_results
    if app_state:
        context["app_state"] = app_state

    with open(os.path.join(folder, "context.json"), "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, default=str)

    notes = [
        f"# Issue Notes — {ts}",
        "",
        "## What fixed it:",
        "",
        "",
        "## What I learned:",
        "",
        "",
        "## Preventative change:",
        "",
        "",
    ]
    with open(os.path.join(folder, "notes.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(notes))

    from core.fix_registry import compute_fingerprint, register_case_fingerprint
    fingerprint = compute_fingerprint(exc_type, exc_value, exc_tb)
    register_case_fingerprint(fingerprint, folder)

    with open(os.path.join(folder, "fingerprint.txt"), "w", encoding="utf-8") as f:
        f.write(fingerprint)

    get_logger("solutions").info(f"Solution folder created: {folder} [fp={fingerprint}]")
    return folder


def export_debug_bundle() -> str:
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    ts = _get_timestamp()
    zip_path = os.path.join(EXPORTS_DIR, f"debug_bundle_{ts}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isdir(LOGS_DIR):
            for fname in sorted(os.listdir(LOGS_DIR)):
                fpath = os.path.join(LOGS_DIR, fname)
                if os.path.isfile(fpath):
                    zf.write(fpath, f"logs/{fname}")

        if os.path.isdir(CRASHES_DIR):
            crash_files = sorted(os.listdir(CRASHES_DIR))
            if crash_files:
                latest = crash_files[-1]
                fpath = os.path.join(CRASHES_DIR, latest)
                if os.path.isfile(fpath):
                    zf.write(fpath, f"crashes/{latest}")

        if os.path.isdir(SOLUTIONS_DIR):
            issue_dirs = sorted(os.listdir(SOLUTIONS_DIR))
            if issue_dirs:
                latest_dir = issue_dirs[-1]
                dir_path = os.path.join(SOLUTIONS_DIR, latest_dir)
                if os.path.isdir(dir_path):
                    for fname in os.listdir(dir_path):
                        fpath = os.path.join(dir_path, fname)
                        if os.path.isfile(fpath):
                            zf.write(fpath, f"solutions/{latest_dir}/{fname}")

    get_logger("export").info(f"Debug bundle exported: {zip_path}")
    return zip_path
