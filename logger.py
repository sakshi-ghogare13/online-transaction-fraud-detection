import logging

logger = logging.getLogger("Fraud Detection")
logger.setLevel(logging.INFO)
file_handler= logging.FileHandler("fraud.log")
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.info("Logger started successfully")