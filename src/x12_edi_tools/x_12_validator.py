from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class Segment:
    id: str
    elements: List[str]

class X12ValidatorError(Exception):
    """Custom exception for X12Validator errors."""

class X12Validator:
    """
    A robust validator for X12 EDI files.
    
    This class provides methods to validate X12 files for compliance with standards,
    with support for different X12 versions and transaction sets.
    """

    SEGMENT_TERMINATOR = '~'
    ELEMENT_SEPARATOR = '*'
    SUB_ELEMENT_SEPARATOR = ':'
    
    def __init__(self):
        self.segments: List[Segment] = []
        self.version: Optional[str] = None
        self.transaction_set_type: Optional[str] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, x12_content: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the X12 content for compliance with standards.
        
        Args:
            x12_content (str): The X12 EDI content as a string.
        
        Returns:
            Tuple[bool, List[str], List[str]]: A tuple containing:
                - Boolean indicating if the validation passed (True) or failed (False)
                - List of error messages
                - List of warning messages
        
        Raises:
            X12ValidatorError: If validation fails due to critical errors.
        """
        x12_content = x12_content.replace("\n", "")
        try:
            self._parse_x12_content(x12_content)
            self._validate_structure()
            self._validate_control_segments()
            self._validate_transaction_set()
            return len(self.errors) == 0, self.errors, self.warnings
        except Exception as e:
            raise X12ValidatorError(f"Failed to validate X12 content: {str(e)}") from e

    def _parse_x12_content(self, x12_content: str) -> None:
        """Parse the X12 content into segments."""
        segments = x12_content.strip().split(self.SEGMENT_TERMINATOR)
        for segment in segments:
            if segment:
                elements = segment.split(self.ELEMENT_SEPARATOR)
                self.segments.append(Segment(id=elements[0], elements=elements[1:]))

    def _validate_structure(self) -> None:
        """Validate the overall structure of the X12 document."""
        if not self.segments:
            self.errors.append("X12 document is empty")
            return

        required_segments = ['ISA', 'GS', 'ST', 'SE', 'GE', 'IEA']
        segment_ids = [seg.id for seg in self.segments]

        for segment in required_segments:
            if segment not in segment_ids:
                self.errors.append(f"Missing required segment: {segment}")

        if self.segments[0].id != 'ISA' or self.segments[-1].id != 'IEA':
            self.errors.append("X12 document must start with ISA and end with IEA")

    def _validate_control_segments(self) -> None:
        """Validate the control segments (ISA, GS, ST, SE, GE, IEA)."""
        self._validate_isa_segment()
        self._validate_gs_segment()
        self._validate_st_segment()
        self._validate_se_segment()
        self._validate_ge_segment()
        self._validate_iea_segment()

    def _validate_isa_segment(self) -> None:
        """Validate the ISA (Interchange Control Header) segment."""
        isa = next((seg for seg in self.segments if seg.id == 'ISA'), None)
        if isa and len(isa.elements) == 16:
            self.version = isa.elements[11]
        else:
            self.errors.append("Invalid ISA segment")

    def _validate_gs_segment(self) -> None:
        """Validate the GS (Functional Group Header) segment."""
        gs = next((seg for seg in self.segments if seg.id == 'GS'), None)
        if gs and len(gs.elements) >= 8:
            if not gs.elements[7].startswith(self.version.split('X')[0]):
                self.errors.append("GS version does not match ISA version")
        else:
            self.errors.append("Invalid GS segment")

    def _validate_st_segment(self) -> None:
        """Validate the ST (Transaction Set Header) segment."""
        st = next((seg for seg in self.segments if seg.id == 'ST'), None)
        if st and len(st.elements) >= 2:
            self.transaction_set_type = st.elements[0]
        else:
            self.errors.append("Invalid ST segment")

    def _validate_se_segment(self) -> None:
        """Validate the SE (Transaction Set Trailer) segment."""
        se = next((seg for seg in self.segments if seg.id == 'SE'), None)
        if se and len(se.elements) >= 2:
            if int(se.elements[0]) != len([seg for seg in self.segments if seg.id not in ['ISA', 'GS', 'GE', 'IEA']]):
                self.errors.append("SE segment count does not match actual segment count")
        else:
            self.errors.append("Invalid SE segment")

    def _validate_ge_segment(self) -> None:
        """Validate the GE (Functional Group Trailer) segment."""
        ge = next((seg for seg in self.segments if seg.id == 'GE'), None)
        if ge and len(ge.elements) >= 2:
            if ge.elements[0] != '1':  # Assuming one transaction set per functional group
                self.errors.append("GE segment count does not match number of transaction sets")
        else:
            self.errors.append("Invalid GE segment")

    def _validate_iea_segment(self) -> None:
        """Validate the IEA (Interchange Control Trailer) segment."""
        iea = next((seg for seg in self.segments if seg.id == 'IEA'), None)
        if iea and len(iea.elements) >= 2:
            if iea.elements[0] != '1':  # Assuming one functional group per interchange
                self.errors.append("IEA segment count does not match number of functional groups")
        else:
            self.errors.append("Invalid IEA segment")

    def _validate_transaction_set(self) -> None:
        """Validate the specific transaction set based on the ST segment."""
        if self.transaction_set_type == '837':
            self._validate_837_claim()
        # Add more transaction set validations as needed

    def _validate_837_claim(self) -> None:
        """Validate an 837 (claim) transaction set."""
        required_segments = ['BHT', 'NM1', 'CLM']
        for segment in required_segments:
            if not any(seg.id == segment for seg in self.segments):
                self.errors.append(f"Missing required segment for 837 claim: {segment}")

        # Validate CLM segment
        clm_segments = [seg for seg in self.segments if seg.id == 'CLM']
        if not clm_segments:
            self.errors.append("No CLM segment found in 837 claim")
        else:
            for clm in clm_segments:
                if len(clm.elements) < 5:
                    self.errors.append("Invalid CLM segment in 837 claim")
                elif not re.match(r'^\d+(\.\d{2})?$', clm.elements[2]):
                    self.errors.append("Invalid monetary amount in CLM segment")

    def __repr__(self) -> str:
        """Provide a string representation of the validator state."""
        return (f"X12Validator(version={self.version}, "
                f"transaction_set_type={self.transaction_set_type}, "
                f"error_count={len(self.errors)}, "
                f"warning_count={len(self.warnings)})")
