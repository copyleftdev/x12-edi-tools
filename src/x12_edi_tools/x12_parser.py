from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Segment:
    id: str
    elements: List[str]

class X12ParserError(Exception):
    """Custom exception for X12Parser errors."""

class X12Parser:
    """
    A robust parser for X12 EDI files.
    
    This class provides methods to parse X12 files into Python objects,
    with support for different X12 versions and transaction sets.
    """

    SEGMENT_TERMINATOR = '~'
    ELEMENT_SEPARATOR = '*'
    
    def __init__(self):
        self.parsed_data: Dict[str, List[Segment]] = defaultdict(list)
        self.transaction_set_header: Optional[Segment] = None
        self.version: Optional[str] = None

    def parse(self, x12_content: str) -> Dict[str, List[Segment]]:
        """
        Parse the X12 content into a structured format.
        
        Args:
            x12_content (str): The X12 EDI content as a string.
        
        Returns:
            Dict[str, List[Segment]]: Parsed X12 data organized by segment type.
        
        Raises:
            X12ParserError: If parsing fails or required segments are missing.
        """
        try:
            segments = self._split_into_segments(x12_content)
            self._process_segments(segments)
            self._validate_parsed_data()
            return dict(self.parsed_data)
        except Exception as e:
            raise X12ParserError(f"Failed to parse X12 content: {str(e)}") from e

    def _split_into_segments(self, x12_content: str) -> List[str]:
        """Split the X12 content into individual segments."""
        return [seg.strip() for seg in x12_content.split(self.SEGMENT_TERMINATOR) if seg.strip()]

    def _process_segments(self, segments: List[str]) -> None:
        """Process each segment and organize them into the parsed_data structure."""
        for segment in segments:
            elements = segment.split(self.ELEMENT_SEPARATOR)
            segment_id = elements[0]
            parsed_segment = Segment(id=segment_id, elements=elements[1:])
            
            if segment_id == 'ISA':
                self._process_isa_segment(parsed_segment)
            elif segment_id == 'GS':
                self._process_gs_segment(parsed_segment)
            elif segment_id == 'ST':
                self._process_st_segment(parsed_segment)
            
            self.parsed_data[segment_id].append(parsed_segment)

    def _process_isa_segment(self, segment: Segment) -> None:
        """Process the ISA (Interchange Control Header) segment."""
        if len(segment.elements) < 16:
            raise X12ParserError("Invalid ISA segment")
        self.version = segment.elements[11]

    def _process_gs_segment(self, segment: Segment) -> None:
        """Process the GS (Functional Group Header) segment."""
        if len(segment.elements) < 8:
            raise X12ParserError("Invalid GS segment")
        # Additional GS segment processing can be added here

    def _process_st_segment(self, segment: Segment) -> None:
        """Process the ST (Transaction Set Header) segment."""
        if len(segment.elements) < 2:
            raise X12ParserError("Invalid ST segment")
        self.transaction_set_header = segment

    def _validate_parsed_data(self) -> None:
        """Validate the parsed data for required segments and structure."""
        required_segments = ['ISA', 'GS', 'ST', 'SE', 'GE', 'IEA']
        for segment in required_segments:
            if segment not in self.parsed_data:
                raise X12ParserError(f"Missing required segment: {segment}")
        
        if not self.version:
            raise X12ParserError("Failed to determine X12 version")

    def get_transaction_set_type(self) -> Optional[str]:
        """
        Get the transaction set type from the ST segment.
        
        Returns:
            Optional[str]: The transaction set type (e.g., '837' for claims) or None if not available.
        """
        if self.transaction_set_header and len(self.transaction_set_header.elements) > 0:
            return self.transaction_set_header.elements[0]
        return None

    def get_segment_count(self, segment_id: str) -> int:
        """
        Get the count of a specific segment type in the parsed data.
        
        Args:
            segment_id (str): The segment identifier (e.g., 'CLM' for claim segments).
        
        Returns:
            int: The count of the specified segment type.
        """
        return len(self.parsed_data.get(segment_id, []))

    def get_elements(self, segment_id: str, occurrence: int = 0) -> List[str]:
        """
        Get the elements of a specific segment occurrence.
        
        Args:
            segment_id (str): The segment identifier.
            occurrence (int): The occurrence of the segment (default is 0 for the first occurrence).
        
        Returns:
            List[str]: The elements of the specified segment occurrence.
        
        Raises:
            X12ParserError: If the specified segment or occurrence is not found.
        """
        segments = self.parsed_data.get(segment_id, [])
        if not segments or occurrence >= len(segments):
            raise X12ParserError(f"Segment {segment_id} occurrence {occurrence} not found")
        return segments[occurrence].elements

    def __repr__(self) -> str:
        """Provide a string representation of the parser state."""
        return (f"X12Parser(version={self.version}, "
                f"transaction_set_type={self.get_transaction_set_type()}, "
                f"segment_count={len(self.parsed_data)})")