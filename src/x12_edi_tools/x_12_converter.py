import json
import csv
from typing import List, Dict, Any, Union
from io import StringIO

class X12ConverterError(Exception):
    """Custom exception for X12Converter errors."""

class X12Converter:
    """
    A robust converter for X12 EDI data to JSON and CSV formats.
    
    This class provides methods to convert X12 data into more readable and processable formats.
    """

    SEGMENT_TERMINATOR = '~'
    ELEMENT_SEPARATOR = '*'
    
    def __init__(self):
        self.segments: List[Dict[str, Any]] = []

    def convert(self, x12_content: str, output_format: str) -> Union[str, StringIO]:
        """
        Convert X12 content to the specified output format.
        
        Args:
            x12_content (str): The X12 EDI content as a string.
            output_format (str): The desired output format ('json' or 'csv').
        
        Returns:
            Union[str, StringIO]: The converted data as a JSON string or CSV StringIO object.
        
        Raises:
            X12ConverterError: If conversion fails or the output format is invalid.
        """
        try:
            self._parse_x12(x12_content)
            if output_format.lower() == 'json':
                return self._to_json()
            elif output_format.lower() == 'csv':
                return self._to_csv()
            else:
                raise X12ConverterError(f"Invalid output format: {output_format}")
        except Exception as e:
            raise X12ConverterError(f"Failed to convert X12 content: {str(e)}") from e

    def _parse_x12(self, x12_content: str) -> None:
        """Parse the X12 content into a list of segment dictionaries."""
        self.segments = []
        for segment in x12_content.strip().split(self.SEGMENT_TERMINATOR):
            if segment:
                elements = segment.split(self.ELEMENT_SEPARATOR)
                self.segments.append({
                    "id": elements[0],
                    "elements": elements[1:]
                })

    def _to_json(self) -> str:
        """Convert the parsed X12 data to a JSON string."""
        return json.dumps(self.segments, indent=2)

    def _to_csv(self) -> StringIO:
        """Convert the parsed X12 data to a CSV format."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Segment ID", "Element 1", "Element 2", "Element 3", "Element 4", "Element 5"])
        
        # Write data
        for segment in self.segments:
            row = [segment["id"]] + segment["elements"]
            writer.writerow(row[:6])  # Limit to 6 columns for readability
        
        output.seek(0)
        return output

    def get_segment_count(self) -> int:
        """Get the count of segments in the parsed X12 data."""
        return len(self.segments)

    def get_segment_types(self) -> List[str]:
        """Get a list of unique segment types in the parsed X12 data."""
        return list(set(segment["id"] for segment in self.segments))

    def get_segments_by_type(self, segment_type: str) -> List[Dict[str, Any]]:
        """Get all segments of a specific type from the parsed X12 data."""
        return [segment for segment in self.segments if segment["id"] == segment_type]

    def __repr__(self) -> str:
        """Provide a string representation of the converter state."""
        return f"X12Converter(segment_count={self.get_segment_count()}, segment_types={self.get_segment_types()})"