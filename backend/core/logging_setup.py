import atexit
import sys
import logging
import zipfile
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path

# Constants for Logging
LOG_ROOT = Path(__file__).resolve().parent.parent.parent / ".log"
BACKEND_LOG_DIR = LOG_ROOT / "backend"

_cleanup_registered = False

def setup_logging(service_name: str = "GameMaster") -> logging.Logger:
    """
    Sets up logging with the specific requirements:
    - Log to console and file.
    - File in .log/<Service_Name>/
    - Naming convention: <Service_Name>-MM-DD-YYYY--HH.log
    - Rotation every couple of hours (we'll set to 1 hour for 'HH' correctness).
    """
    global _cleanup_registered
    
    # Ensure log directory exists
    log_dir = LOG_ROOT / service_name
    log_dir.mkdir(parents=True, exist_ok=True)

    current_time = datetime.now()
    log_filename = f"{service_name}-{current_time.strftime('%m-%d-%Y--%H')}.log"
    log_file_path = log_dir / log_filename

    # Create Logger
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    
    # Check if handlers already exist to avoid adding duplicates
    if not logger.handlers:
        # 1. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 2. File Handler (Timed Rotating)
        file_handler = TimedRotatingFileHandler(
            filename=log_file_path,
            when="H",
            interval=1,
            backupCount=24,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Register cleanup on exit (only once per process)
    if not _cleanup_registered:
        atexit.register(cleanup_logs)
        _cleanup_registered = True

    logger.info(f"Logging initialized for {service_name} at {log_file_path}")
    return logger


def cleanup_logs():
    """
    Compresses logs from previous days into .zip files and removes the raw files.
    """
    if not LOG_ROOT.exists():
        return
    
    today_str = datetime.now().strftime('%m-%d-%Y')
    
    for service_dir in LOG_ROOT.iterdir():
        if service_dir.is_dir() and service_dir.name != "README.md":
            _archive_service_logs(service_dir, today_str)


def _archive_service_logs(service_dir: Path, today_str: str):
    logs_to_zip = []
    for log_file in service_dir.glob("*.log"):
        # Check if file name contains today's date. If NOT, zip it.
        if today_str not in log_file.name:
            logs_to_zip.append(log_file)
    
    if logs_to_zip:
        zip_name = service_dir / f"archive-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.zip"
        try:
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for log in logs_to_zip:
                    zipf.write(log, log.name)
            
            # Uncomment to enable deletion after zipping
            # for log in logs_to_zip:
            #     os.remove(log)
                
            print(f"[LOG_CLEANUP] Archived {len(logs_to_zip)} logs to {zip_name}")
        except Exception as e:
            print(f"[LOG_CLEANUP] Error archiving logs in {service_dir}: {e}")
