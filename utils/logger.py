# utils/logger.py (yangi fayl)
import logging
from datetime import datetime

def setup_logger():
    logger = logging.getLogger("tahlilchi")
    logger.setLevel(logging.INFO)
    
    # Console chiqish
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()