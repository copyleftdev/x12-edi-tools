import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import json
import base64
from io import BytesIO

@dataclass
class X12Segment:
    segment_id: str
    elements: List[str]

class X12VisualizerError(Exception):
    """Custom exception for X12Visualizer errors."""

class X12Visualizer:
    """
    A robust visualizer for X12 EDI data.
    
    This class provides methods to create visual representations of X12 data,
    including transaction flow diagrams and data distribution charts.
    """
    
    def __init__(self):
        """Initialize the X12Visualizer."""
        self.plt = plt
        self.plt.style.use('ggplot')

    def create_transaction_flow_diagram(self, segments: List[X12Segment]) -> str:
        """
        Create a transaction flow diagram based on X12 segments.
        
        Args:
            segments (List[X12Segment]): List of X12 segments.
        
        Returns:
            str: Base64 encoded PNG image of the diagram.
        
        Raises:
            X12VisualizerError: If creating the diagram fails.
        """
        try:
            G = nx.DiGraph()
            for i, segment in enumerate(segments):
                G.add_node(i, label=f"{segment.segment_id}\n{' '.join(segment.elements[:2])}")
                if i > 0:
                    G.add_edge(i-1, i)

            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G)
            nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                    node_size=3000, font_size=8, font_weight='bold')
            
            labels = nx.get_node_attributes(G, 'label')
            nx.draw_networkx_labels(G, pos, labels, font_size=8)

            return self._fig_to_base64()
        except Exception as e:
            raise X12VisualizerError(f"Failed to create transaction flow diagram: {str(e)}")

    def create_segment_distribution_chart(self, segments: List[X12Segment]) -> str:
        """
        Create a bar chart showing the distribution of segment types.
        
        Args:
            segments (List[X12Segment]): List of X12 segments.
        
        Returns:
            str: Base64 encoded PNG image of the chart.
        
        Raises:
            X12VisualizerError: If creating the chart fails.
        """
        try:
            segment_counts = {}
            for segment in segments:
                segment_counts[segment.segment_id] = segment_counts.get(segment.segment_id, 0) + 1

            plt.figure(figsize=(12, 6))
            plt.bar(segment_counts.keys(), segment_counts.values())
            plt.title('Distribution of X12 Segments')
            plt.xlabel('Segment Type')
            plt.ylabel('Count')
            plt.xticks(rotation=45)

            return self._fig_to_base64()
        except Exception as e:
            raise X12VisualizerError(f"Failed to create segment distribution chart: {str(e)}")

    def create_element_length_boxplot(self, segments: List[X12Segment]) -> str:
        """
        Create a box plot showing the distribution of element lengths for each segment type.
        
        Args:
            segments (List[X12Segment]): List of X12 segments.
        
        Returns:
            str: Base64 encoded PNG image of the box plot.
        
        Raises:
            X12VisualizerError: If creating the box plot fails.
        """
        try:
            segment_lengths = {}
            for segment in segments:
                if segment.segment_id not in segment_lengths:
                    segment_lengths[segment.segment_id] = []
                segment_lengths[segment.segment_id].extend([len(elem) for elem in segment.elements])

            plt.figure(figsize=(12, 6))
            plt.boxplot(segment_lengths.values(), labels=segment_lengths.keys())
            plt.title('Distribution of Element Lengths by Segment Type')
            plt.xlabel('Segment Type')
            plt.ylabel('Element Length')
            plt.xticks(rotation=45)

            return self._fig_to_base64()
        except Exception as e:
            raise X12VisualizerError(f"Failed to create element length box plot: {str(e)}")

    def create_transaction_summary(self, segments: List[X12Segment]) -> Dict[str, Any]:
        """
        Create a summary of the transaction including key-value pairs and statistics.
        
        Args:
            segments (List[X12Segment]): List of X12 segments.
        
        Returns:
            Dict[str, Any]: A dictionary containing transaction summary.
        
        Raises:
            X12VisualizerError: If creating the summary fails.
        """
        try:
            summary = {
                "total_segments": len(segments),
                "segment_types": len(set(seg.segment_id for seg in segments)),
                "key_values": {},
                "statistics": {}
            }

            # Extract key-value pairs
            for segment in segments:
                if segment.segment_id in ['ISA', 'GS', 'ST', 'SE', 'GE', 'IEA']:
                    summary["key_values"][segment.segment_id] = ' '.join(segment.elements)

            # Calculate statistics
            element_counts = [len(seg.elements) for seg in segments]
            summary["statistics"]["avg_elements_per_segment"] = sum(element_counts) / len(element_counts)
            summary["statistics"]["max_elements"] = max(element_counts)
            summary["statistics"]["min_elements"] = min(element_counts)

            return summary
        except Exception as e:
            raise X12VisualizerError(f"Failed to create transaction summary: {str(e)}")

    def _fig_to_base64(self) -> str:
        """Convert the current matplotlib figure to a base64 encoded PNG."""
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    def __repr__(self) -> str:
        """Provide a string representation of the X12Visualizer."""
        return "X12Visualizer()"
    

    # Sample X12 segments (this would usually come from parsing an actual X12 file)
segments = [
    X12Segment("ISA", ["00", "          ", "00", "          ", "ZZ", "SENDER123", "ZZ", "RECEIVER456", "230701", "1200", "^", "00501", "000000001", "0", "P", ":"]),
    X12Segment("GS", ["HC", "SENDER123", "RECEIVER456", "20230701", "1200", "1", "X", "005010X222A1"]),
    X12Segment("ST", ["837", "0001"]),
    X12Segment("BHT", ["0019", "00", "1", "20230701", "1200", "CH"]),
    X12Segment("NM1", ["41", "2", "SUBMITTER NAME", "", "", "", "", "46", "12345"]),
    X12Segment("PER", ["IC", "CONTACT NAME", "TE", "1234567890"]),
    X12Segment("NM1", ["1P", "2", "BILLING PROVIDER", "", "", "", "", "XX", "1234567890"]),
    X12Segment("N3", ["123 BILLING ST"]),
    X12Segment("N4", ["CITY", "ST", "12345"]),
    X12Segment("SE", ["20", "0001"]),
    X12Segment("GE", ["1", "1"]),
    X12Segment("IEA", ["1", "000000001"])
]

visualizer = X12Visualizer()

try:
    # Create and save transaction flow diagram
    flow_diagram = visualizer.create_transaction_flow_diagram(segments)
    with open("transaction_flow.png", "wb") as f:
        f.write(base64.b64decode(flow_diagram))
    print("Transaction flow diagram saved as 'transaction_flow.png'")

    # Create and save segment distribution chart
    dist_chart = visualizer.create_segment_distribution_chart(segments)
    with open("segment_distribution.png", "wb") as f:
        f.write(base64.b64decode(dist_chart))
    print("Segment distribution chart saved as 'segment_distribution.png'")

    # Create and save element length boxplot
    boxplot = visualizer.create_element_length_boxplot(segments)
    with open("element_length_boxplot.png", "wb") as f:
        f.write(base64.b64decode(boxplot))
    print("Element length boxplot saved as 'element_length_boxplot.png'")

    # Get transaction summary
    summary = visualizer.create_transaction_summary(segments)
    print("\nTransaction Summary:")
    print(json.dumps(summary, indent=2))

except X12VisualizerError as e:
    print(f"Visualization error: {e}")