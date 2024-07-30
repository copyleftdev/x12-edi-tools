import re
from typing import List, Dict, Optional
import csv
import os
from dataclasses import dataclass

@dataclass
class CDTCode:
    code: str
    description: str
    category: str

class DentalCodeValidatorError(Exception):
    """Custom exception for DentalCodeValidator errors."""

class DentalCodeValidator:
    """
    A robust validator for dental procedure codes (CDT codes) used in X12 transactions.
    
    This class provides methods to validate CDT codes, check for obsolete codes,
    and provide descriptions for valid codes.
    """
    
    def __init__(self, cdt_file_path: Optional[str] = None):
        """
        Initialize the DentalCodeValidator.
        
        Args:
            cdt_file_path (Optional[str]): Path to a CSV file containing CDT codes.
                If not provided, a default set of codes will be used.
        
        Raises:
            DentalCodeValidatorError: If the CDT file cannot be loaded.
        """
        self.cdt_codes: Dict[str, CDTCode] = {}
        self.load_cdt_codes(cdt_file_path)

    def load_cdt_codes(self, file_path: Optional[str] = None) -> None:
        """
        Load CDT codes from a CSV file or use a default set.
        
        Args:
            file_path (Optional[str]): Path to a CSV file containing CDT codes.
        
        Raises:
            DentalCodeValidatorError: If the file cannot be loaded or parsed.
        """
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        code = row['code'].strip()
                        self.cdt_codes[code] = CDTCode(
                            code=code,
                            description=row['description'].strip(),
                            category=row['category'].strip()
                        )
            except Exception as e:
                raise DentalCodeValidatorError(f"Failed to load CDT codes from file: {str(e)}")
        else:
            # Use a default set of codes if no file is provided
            self._load_default_codes()

    def _load_default_codes(self) -> None:
        """Load a default set of CDT codes."""
        default_codes = [
            ("D0120", "Periodic oral evaluation", "Diagnostic"),
            ("D0150", "Comprehensive oral evaluation", "Diagnostic"),
            ("D0220", "Intraoral - periapical first radiographic image", "Diagnostic"),
            ("D1110", "Prophylaxis - adult", "Preventive"),
            ("D2150", "Amalgam - two surfaces, primary or permanent", "Restorative"),
            ("D2740", "Crown - porcelain/ceramic", "Restorative"),
        ]
        for code, description, category in default_codes:
            self.cdt_codes[code] = CDTCode(code, description, category)

    def validate_code(self, code: str) -> bool:
        """
        Validate a single CDT code.
        
        Args:
            code (str): The CDT code to validate.
        
        Returns:
            bool: True if the code is valid, False otherwise.
        """
        return code in self.cdt_codes

    def validate_codes(self, codes: List[str]) -> Dict[str, bool]:
        """
        Validate a list of CDT codes.
        
        Args:
            codes (List[str]): A list of CDT codes to validate.
        
        Returns:
            Dict[str, bool]: A dictionary with codes as keys and validation results as values.
        """
        return {code: self.validate_code(code) for code in codes}

    def get_code_description(self, code: str) -> Optional[str]:
        """
        Get the description for a CDT code.
        
        Args:
            code (str): The CDT code to look up.
        
        Returns:
            Optional[str]: The description of the code if valid, None otherwise.
        """
        cdt_code = self.cdt_codes.get(code)
        return cdt_code.description if cdt_code else None

    def get_code_category(self, code: str) -> Optional[str]:
        """
        Get the category for a CDT code.
        
        Args:
            code (str): The CDT code to look up.
        
        Returns:
            Optional[str]: The category of the code if valid, None otherwise.
        """
        cdt_code = self.cdt_codes.get(code)
        return cdt_code.category if cdt_code else None

    def validate_code_format(self, code: str) -> bool:
        """
        Validate the format of a CDT code.
        
        Args:
            code (str): The CDT code to validate.
        
        Returns:
            bool: True if the format is valid, False otherwise.
        """
        return bool(re.match(r'^D\d{4}$', code))

    def find_similar_codes(self, code: str, max_distance: int = 1) -> List[str]:
        """
        Find similar CDT codes based on Levenshtein distance.
        
        Args:
            code (str): The CDT code to find similar codes for.
            max_distance (int): The maximum Levenshtein distance to consider.
        
        Returns:
            List[str]: A list of similar CDT codes.
        """
        similar_codes = []
        for valid_code in self.cdt_codes:
            if self._levenshtein_distance(code, valid_code) <= max_distance:
                similar_codes.append(valid_code)
        return similar_codes

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate the Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return DentalCodeValidator._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def __repr__(self) -> str:
        """Provide a string representation of the DentalCodeValidator."""
        return f"DentalCodeValidator(code_count={len(self.cdt_codes)})"