import logging
from typing import Dict, Any, Optional
import os
import json
from datetime import datetime

class X12LoggerError(Exception):
    """Custom exception for X12Logger errors."""

class X12Logger:
    """
    A robust logging system for X12 EDI operations.
    
    This class provides methods to log various X12 operations, including
    parsing, generation, validation, and transmission of X12 messages.
    It supports both file-based and console logging, as well as different
    log levels for fine-grained control over log output.
    """
    
    def __init__(self, log_directory: str, console_output: bool = True, log_level: str = "INFO"):
        """
        Initialize the X12Logger.
        
        Args:
            log_directory (str): Directory to save log files.
            console_output (bool): Whether to output logs to console as well.
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        
        Raises:
            X12LoggerError: If logger initialization fails.
        """
        self.log_directory = log_directory
        self.console_output = console_output
        self.log_level = self._get_log_level(log_level)
        
        try:
            self._setup_logger()
        except Exception as e:
            raise X12LoggerError(f"Failed to initialize logger: {str(e)}")

    def _setup_logger(self):
        """Set up the logger with file and console handlers."""
        self.logger = logging.getLogger("X12Logger")
        self.logger.setLevel(self.log_level)
        
        # Create log directory if it doesn't exist
        os.makedirs(self.log_directory, exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(
            os.path.join(self.log_directory, f"x12_log_{datetime.now().strftime('%Y%m%d')}.log")
        )
        file_handler.setLevel(self.log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def _get_log_level(self, level: str) -> int:
        """Convert string log level to logging module constant."""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(level.upper(), logging.INFO)

    def log_parse(self, transaction_type: str, file_path: str, result: Dict[str, Any]):
        """Log X12 parsing operation."""
        self.logger.info(f"Parsed X12 {transaction_type} from {file_path}")
        self.logger.debug(f"Parse result: {json.dumps(result, indent=2)}")

    def log_generate(self, transaction_type: str, file_path: str, data: Dict[str, Any]):
        """Log X12 generation operation."""
        self.logger.info(f"Generated X12 {transaction_type} to {file_path}")
        self.logger.debug(f"Generation data: {json.dumps(data, indent=2)}")

    def log_validate(self, transaction_type: str, file_path: str, is_valid: bool, errors: Optional[List[str]] = None):
        """Log X12 validation operation."""
        status = "passed" if is_valid else "failed"
        self.logger.info(f"Validation {status} for X12 {transaction_type} file: {file_path}")
        if errors:
            for error in errors:
                self.logger.warning(f"Validation error: {error}")

    def log_transmit(self, transaction_type: str, file_path: str, destination: str, status: str):
        """Log X12 transmission operation."""
        self.logger.info(f"Transmitted X12 {transaction_type} file: {file_path} to {destination}")
        self.logger.info(f"Transmission status: {status}")

    def log_receive(self, transaction_type: str, file_path: str, source: str):
        """Log X12 receive operation."""
        self.logger.info(f"Received X12 {transaction_type} file: {file_path} from {source}")

    def log_error(self, operation: str, error_message: str):
        """Log X12 operation errors."""
        self.logger.error(f"Error during {operation}: {error_message}")

    def log_custom(self, level: str, message: str):
        """Log custom messages at specified level."""
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(message)

    def get_latest_logs(self, count: int = 10) -> List[str]:
        """
        Retrieve the latest log entries.
        
        Args:
            count (int): Number of log entries to retrieve.
        
        Returns:
            List[str]: List of the latest log entries.
        """
        log_file = os.path.join(self.log_directory, f"x12_log_{datetime.now().strftime('%Y%m%d')}.log")
        if not os.path.exists(log_file):
            return []
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            return lines[-count:]

    def __repr__(self) -> str:
        """Provide a string representation of the X12Logger."""
        return f"X12Logger(log_directory='{self.log_directory}', console_output={self.console_output}, log_level='{logging.getLevelName(self.log_level)}')"