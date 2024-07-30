import os
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import logging

@dataclass
class ProcessingResult:
    filename: str
    success: bool
    message: str
    data: Any = None

class BatchProcessorError(Exception):
    """Custom exception for BatchProcessor errors."""

class BatchProcessor:
    """
    A robust batch processor for X12 files.
    
    This class provides methods to process multiple X12 files in batch mode,
    with support for parallel processing and customizable processing functions.
    """
    
    def __init__(self, input_directory: str, output_directory: str, max_workers: int = 4):
        """
        Initialize the BatchProcessor.
        
        Args:
            input_directory (str): Path to the directory containing input X12 files.
            output_directory (str): Path to the directory for output files.
            max_workers (int): Maximum number of worker threads for parallel processing.
        
        Raises:
            BatchProcessorError: If the directories are invalid.
        """
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.max_workers = max_workers
        self.logger = self._setup_logger()

        self._validate_directories()

    def process_batch(self, processing_func: Callable[[str, str], Any]) -> List[ProcessingResult]:
        """
        Process a batch of X12 files.
        
        Args:
            processing_func (Callable[[str, str], Any]): Function to process each file.
                It should take input and output file paths as arguments.
        
        Returns:
            List[ProcessingResult]: List of processing results for each file.
        """
        x12_files = self._get_x12_files()
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._process_file, file, processing_func): file
                for file in x12_files
            }
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(f"Processed {file}: {result.message}")
                except Exception as e:
                    self.logger.error(f"Error processing {file}: {str(e)}")
                    results.append(ProcessingResult(file, False, str(e)))

        return results

    def generate_summary(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """
        Generate a summary of the batch processing results.
        
        Args:
            results (List[ProcessingResult]): List of processing results.
        
        Returns:
            Dict[str, Any]: Summary of the batch processing.
        """
        total_files = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total_files - successful

        summary = {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_files) * 100 if total_files > 0 else 0,
            "failed_files": [r.filename for r in results if not r.success]
        }

        return summary

    def _validate_directories(self) -> None:
        """Validate the input and output directories."""
        if not os.path.isdir(self.input_directory):
            raise BatchProcessorError(f"Invalid input directory: {self.input_directory}")
        if not os.path.isdir(self.output_directory):
            raise BatchProcessorError(f"Invalid output directory: {self.output_directory}")

    def _get_x12_files(self) -> List[str]:
        """Get a list of X12 files in the input directory."""
        return [f for f in os.listdir(self.input_directory) if f.endswith('.x12') or f.endswith('.edi')]

    def _process_file(self, filename: str, processing_func: Callable[[str, str], Any]) -> ProcessingResult:
        """Process a single X12 file."""
        input_path = os.path.join(self.input_directory, filename)
        output_path = os.path.join(self.output_directory, f"processed_{filename}")
        
        try:
            result = processing_func(input_path, output_path)
            return ProcessingResult(filename, True, "Processing successful", result)
        except Exception as e:
            return ProcessingResult(filename, False, f"Processing failed: {str(e)}")

    def _setup_logger(self) -> logging.Logger:
        """Set up a logger for the BatchProcessor."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def __repr__(self) -> str:
        """Provide a string representation of the BatchProcessor."""
        return (f"BatchProcessor(input_directory='{self.input_directory}', "
                f"output_directory='{self.output_directory}', "
                f"max_workers={self.max_workers})")