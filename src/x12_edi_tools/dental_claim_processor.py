from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Claim:
    claim_id: str
    patient_name: str
    patient_dob: datetime
    provider_name: str
    provider_npi: str
    procedures: List[Dict[str, str]]
    total_charge: float

class DentalClaimProcessorError(Exception):
    """Custom exception for DentalClaimProcessor errors."""

class DentalClaimProcessor:
    """
    A robust processor for dental claims in X12 837D format.
    
    This class provides methods to extract relevant information from dental claims
    and process them into a more accessible format.
    """

    def __init__(self):
        self.claims: List[Claim] = []
        self.current_claim: Optional[Claim] = None

    def process(self, x12_content: str) -> List[Claim]:
        """
        Process the X12 837D content and extract dental claims.
        
        Args:
            x12_content (str): The X12 EDI content as a string.
        
        Returns:
            List[Claim]: A list of processed Claim objects.
        
        Raises:
            DentalClaimProcessorError: If processing fails or required segments are missing.
        """
        try:
            segments = self._split_into_segments(x12_content)
            self._process_segments(segments)
            return self.claims
        except Exception as e:
            raise DentalClaimProcessorError(f"Failed to process dental claims: {str(e)}") from e

    def _split_into_segments(self, x12_content: str) -> List[List[str]]:
        """Split the X12 content into individual segments and elements."""
        segments = x12_content.strip().split('~')
        return [seg.split('*') for seg in segments if seg]

    def _process_segments(self, segments: List[List[str]]) -> None:
        """Process each segment and extract claim information."""
        for segment in segments:
            if not segment:
                continue
            
            segment_id = segment[0]
            
            if segment_id == 'ST':
                self._validate_transaction_set(segment)
            elif segment_id == 'CLM':
                self._process_clm_segment(segment)
            elif segment_id == 'NM1':
                self._process_nm1_segment(segment)
            elif segment_id == 'DMG':
                self._process_dmg_segment(segment)
            elif segment_id == 'SV3':
                self._process_sv3_segment(segment)
            elif segment_id == 'SE':
                self._finalize_current_claim()

    def _validate_transaction_set(self, segment: List[str]) -> None:
        """Validate that this is a dental claim transaction set."""
        if len(segment) < 3 or segment[1] != '837' or segment[2] != 'D':
            raise DentalClaimProcessorError("Invalid or non-dental claim transaction set")

    def _process_clm_segment(self, segment: List[str]) -> None:
        """Process the CLM (Claim) segment."""
        if len(segment) < 3:
            raise DentalClaimProcessorError("Invalid CLM segment")
        
        self._finalize_current_claim()  # Finalize previous claim if exists
        
        self.current_claim = Claim(
            claim_id=segment[1],
            patient_name="",
            patient_dob=datetime.now(),  # Placeholder, will be updated later
            provider_name="",
            provider_npi="",
            procedures=[],
            total_charge=float(segment[2])
        )

    def _process_nm1_segment(self, segment: List[str]) -> None:
        """Process the NM1 (Name) segment."""
        if not self.current_claim or len(segment) < 4:
            return

        entity_identifier = segment[1]
        name = f"{segment[3]} {segment[2]}".strip()

        if entity_identifier == 'QC':  # Patient
            self.current_claim.patient_name = name
        elif entity_identifier == '85':  # Billing Provider
            self.current_claim.provider_name = name
            if len(segment) > 9:
                self.current_claim.provider_npi = segment[9]

    def _process_dmg_segment(self, segment: List[str]) -> None:
        """Process the DMG (Demographics) segment."""
        if not self.current_claim or len(segment) < 3:
            return

        if segment[1] == 'D8':  # Date format
            try:
                self.current_claim.patient_dob = datetime.strptime(segment[2], '%Y%m%d')
            except ValueError:
                raise DentalClaimProcessorError(f"Invalid date format in DMG segment: {segment[2]}")

    def _process_sv3_segment(self, segment: List[str]) -> None:
        """Process the SV3 (Dental Service) segment."""
        if not self.current_claim or len(segment) < 4:
            return

        procedure = {
            "code": segment[1],
            "description": segment[2],
            "charge": segment[3]
        }
        self.current_claim.procedures.append(procedure)

    def _finalize_current_claim(self) -> None:
        """Finalize the current claim and add it to the list of processed claims."""
        if self.current_claim:
            self.claims.append(self.current_claim)
            self.current_claim = None

    def get_total_charges(self) -> float:
        """Calculate the total charges for all processed claims."""
        return sum(claim.total_charge for claim in self.claims)

    def get_claim_count(self) -> int:
        """Get the number of processed claims."""
        return len(self.claims)

    def get_claim_by_id(self, claim_id: str) -> Optional[Claim]:
        """Retrieve a specific claim by its ID."""
        return next((claim for claim in self.claims if claim.claim_id == claim_id), None)

    def __repr__(self) -> str:
        """Provide a string representation of the processor state."""
        return (f"DentalClaimProcessor(processed_claims={len(self.claims)}, "
                f"total_charges={self.get_total_charges():.2f})")