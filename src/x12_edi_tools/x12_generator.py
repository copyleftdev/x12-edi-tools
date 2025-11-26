from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Segment:
    id: str
    elements: List[str]

class X12GeneratorError(Exception):
    """Custom exception for X12Generator errors."""

class X12Generator:
    """
    A robust generator for X12 EDI files.
    
    This class provides methods to create valid X12 files from Python objects,
    with support for different X12 versions and transaction sets.
    """

    SEGMENT_TERMINATOR = '~'
    ELEMENT_SEPARATOR = '*'
    SUB_ELEMENT_SEPARATOR = ':'
    
    def __init__(self, version: str = "005010X222A1"):
        self.version = version
        self.segments: List[Segment] = []
        self.transaction_set_type: Optional[str] = None
        self.control_numbers: Dict[str, int] = defaultdict(int)

    def generate(self) -> str:
        """
        Generate the X12 content from the added segments.
        
        Returns:
            str: The generated X12 EDI content as a string.
        
        Raises:
            X12GeneratorError: If generation fails or required segments are missing.
        """
        try:
            self._validate_segments()
            return self._build_x12_string()
        except Exception as e:
            raise X12GeneratorError(f"Failed to generate X12 content: {str(e)}") from e

    def add_segment(self, segment_id: str, elements: List[str]) -> None:
        """
        Add a segment to the X12 document.
        
        Args:
            segment_id (str): The segment identifier (e.g., 'ISA', 'GS', 'ST').
            elements (List[str]): The elements of the segment.
        """
        self.segments.append(Segment(id=segment_id, elements=elements))

        if segment_id == 'ST':
            self._process_st_segment(elements)

    def set_transaction_set_type(self, transaction_set_type: str) -> None:
        """
        Set the transaction set type for the X12 document.
        
        Args:
            transaction_set_type (str): The transaction set type (e.g., '837' for claims).
        """
        self.transaction_set_type = transaction_set_type

    def _process_st_segment(self, elements: List[str]) -> None:
        """Process the ST (Transaction Set Header) segment."""
        if len(elements) < 2:
            raise X12GeneratorError("Invalid ST segment")
        self.transaction_set_type = elements[0]

    def _validate_segments(self) -> None:
        """Validate the segments for required elements and structure."""
        required_segments = ['ISA', 'GS', 'ST', 'SE', 'GE', 'IEA']
        segment_ids = [seg.id for seg in self.segments]
        
        for segment in required_segments:
            if segment not in segment_ids:
                raise X12GeneratorError(f"Missing required segment: {segment}")
        
        if not self.transaction_set_type:
            raise X12GeneratorError("Transaction set type not specified")

    def _build_x12_string(self) -> str:
        """Build the X12 string from the segments."""
        x12_content = []
        for segment in self.segments:
            segment_str = self.ELEMENT_SEPARATOR.join([segment.id] + segment.elements)
            x12_content.append(segment_str + self.SEGMENT_TERMINATOR)
        return ''.join(x12_content)

    def add_isa_segment(self,
        sender_id: str,
        receiver_id: str,
        sender_qualifier: str = "ZZ",
        receiver_qualifier: str = "ZZ",
        repetition_separator: str = "^",
        ack_requested: bool = False,
        environment_indicator: str = "P",
        sub_element_separator: str = SUB_ELEMENT_SEPARATOR
    ) -> None:
        """
        Add the ISA (Interchange Control Header) segment.
        
        Args:
            sender_id (str): The sender's identification number.
            receiver_id (str): The receiver's identification number.
            sender_qualifier (str): The sender's identification qualifier/type.
            receiver_qualifier (str): The receiver's identification qualifier/type.
            ack_requested (bool): Acknowledgement is requested from receiver for this document.
            environment_indicator (str): "P" = production; "T" = testing.
            sub_element_separator (str): The sub-element separator used in this document.
        """
        self.control_numbers['ISA'] += 1
        isa_elements = [
            "00", "          ", "00", "          ",
            sender_qualifier, sender_id.ljust(15), receiver_qualifier, receiver_id.ljust(15),
            self._get_current_date(), self._get_current_time(),
            repetition_separator, self.version, str(self.control_numbers['ISA']).zfill(9),
            "1" if ack_requested else "0", environment_indicator, sub_element_separator
        ]
        self.add_segment("ISA", isa_elements)

    def add_gs_segment(self,
        func_id_code: str,
        sender_code: str,
        receiver_code: str,
        version_override: str | None = None
    ) -> None:
        """
        Add the GS (Functional Group Header) segment.
        
        Args:
            func_id_code (str): The functional identifier code.
            sender_code (str): The application sender's code.
            receiver_code (str): The application receiver's code.
            version_override (str | None): Optional override for this section from the default version split.
        """
        self.control_numbers['GS'] += 1
        gs_elements = [
            func_id_code, sender_code, receiver_code,
            self._get_current_date(), self._get_current_time(),
            str(self.control_numbers['GS']), "X", version_override or self.version.split("X")[0]
        ]
        self.add_segment("GS", gs_elements)

    def add_st_segment(self) -> None:
        """Add the ST (Transaction Set Header) segment."""
        if not self.transaction_set_type:
            raise X12GeneratorError("Transaction set type must be set before adding ST segment")
        self.control_numbers['ST'] += 1
        st_elements = [
            self.transaction_set_type,
            str(self.control_numbers['ST']).zfill(4)
        ]
        self.add_segment("ST", st_elements)

    def add_se_segment(self) -> None:
        """Add the SE (Transaction Set Trailer) segment."""
        se_elements = [
            str(len(self.segments) + 1),  # +1 to include this SE segment
            str(self.control_numbers['ST']).zfill(4)
        ]
        self.add_segment("SE", se_elements)

    def add_ge_segment(self) -> None:
        """Add the GE (Functional Group Trailer) segment."""
        ge_elements = [
            "1",  # Number of transaction sets included
            str(self.control_numbers['GS'])
        ]
        self.add_segment("GE", ge_elements)

    def add_iea_segment(self) -> None:
        """Add the IEA (Interchange Control Trailer) segment."""
        iea_elements = [
            "1",  # Number of included functional groups
            str(self.control_numbers['ISA']).zfill(9)
        ]
        self.add_segment("IEA", iea_elements)

    def _get_current_date(self) -> str:
        """Get the current date in YYMMDD format."""
        from datetime import datetime
        return datetime.now().strftime("%y%m%d")

    def _get_current_time(self) -> str:
        """Get the current time in HHMM format."""
        from datetime import datetime
        return datetime.now().strftime("%H%M")

    def __repr__(self) -> str:
        """Provide a string representation of the generator state."""
        return (f"X12Generator(version={self.version}, "
                f"transaction_set_type={self.transaction_set_type}, "
                f"segment_count={len(self.segments)})")