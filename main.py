import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from core.logger import setup_logging, write_crash_report, write_solution_folder, get_logger
from core.fix_registry import lookup_fix, compute_fingerprint
from ui.main_window import MainWindow


def _global_exception_handler(exc_type, exc_value, exc_tb):
    logger = get_logger("crash")
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
    _path, fingerprint = write_crash_report(exc_type, exc_value, exc_tb, action="unhandled_exception")
    write_solution_folder(exc_type, exc_value, exc_tb, action="unhandled_exception")
    fix = lookup_fix(fingerprint)
    if fix and fix.get("title"):
        logger.info(f"Known issue detected: {fix['title']} [fp={fingerprint}]")
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main() -> None:
    setup_logging()
    sys.excepthook = _global_exception_handler

    logger = get_logger("main")
    logger.info("Application starting")

    app = QApplication(sys.argv)
    app.setApplicationName("Kingdom Digital Systems - Lyric Performance Engine")
    window = MainWindow()
    window.show()
    logger.info("Main window displayed")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
