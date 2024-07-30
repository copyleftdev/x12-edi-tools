from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class ClaimPayment:
    claim_id: str
    patient_name: str
    charge_amount: Decimal
    payment_amount: Decimal
    patient_responsibility: Decimal
    service_date: datetime
    claim_status: str
    adjustment_reasons: List[Dict[str, str]]

@dataclass
class RemittanceAdvice:
    transaction_id: str
    payer_name: str
    payer_id: str
    payee_name: str
    payee_npi: str
    payment_method: str
    payment_amount: Decimal
    payment_date: datetime
    claims: List[ClaimPayment]

class RemittanceAdviceParserError(Exception):
    """Custom exception for RemittanceAdviceParser errors."""

class RemittanceAdviceParser:
    """
    A robust parser for X12 835 (Electronic Remittance Advice) transactions.
    
    This class provides methods to parse X12 835 files and extract payment and claim information.
    """

    SEGMENT_TERMINATOR = '~'
    ELEMENT_SEPARATOR = '*'
    
    def __init__(self):
        self.remittance_advice: Optional[RemittanceAdvice] = None
        self.current_claim: Optional[ClaimPayment] = None

    def parse(self, x12_content: str) -> RemittanceAdvice:
        """
        Parse the X12 835 content and extract remittance advice information.
        
        Args:
            x12_content (str): The X12 835 EDI content as a string.
        
        Returns:
            RemittanceAdvice: The parsed remittance advice object.
        
        Raises:
            RemittanceAdviceParserError: If parsing fails or required segments are missing.
        """
        try:
            segments = self._split_into_segments(x12_content)
            self._process_segments(segments)
            if not self.remittance_advice:
                raise RemittanceAdviceParserError("Failed to parse remittance advice")
            return self.remittance_advice
        except Exception as e:
            raise RemittanceAdviceParserError(f"Failed to parse remittance advice: {str(e)}") from e

    def _split_into_segments(self, x12_content: str) -> List[List[str]]:
        """Split the X12 content into individual segments and elements."""
        segments = x12_content.strip().split(self.SEGMENT_TERMINATOR)
        return [seg.split(self.ELEMENT_SEPARATOR) for seg in segments if seg]

    def _process_segments(self, segments: List[List[str]]) -> None:
        """Process each segment and extract remittance advice information."""
        for segment in segments:
            if not segment:
                continue
            
            segment_id = segment[0]
            
            if segment_id == 'ST':
                self._validate_transaction_set(segment)
            elif segment_id == 'BPR':
                self._process_bpr_segment(segment)
            elif segment_id == 'TRN':
                self._process_trn_segment(segment)
            elif segment_id == 'N1':
                self._process_n1_segment(segment)
            elif segment_id == 'CLP':
                self._process_clp_segment(segment)
            elif segment_id == 'NM1' and self.current_claim:
                self._process_nm1_segment(segment)
            elif segment_id == 'DTM' and self.current_claim:
                self._process_dtm_segment(segment)
            elif segment_id == 'CAS' and self.current_claim:
                self._process_cas_segment(segment)
            elif segment_id == 'SE':
                self._finalize_current_claim()

    def _validate_transaction_set(self, segment: List[str]) -> None:
        """Validate that this is a remittance advice transaction set."""
        if len(segment) < 3 or segment[1] != '835':
            raise RemittanceAdviceParserError("Invalid or non-remittance advice transaction set")

    def _process_bpr_segment(self, segment: List[str]) -> None:
        """Process the BPR (Financial Information) segment."""
        if len(segment) < 16:
            raise RemittanceAdviceParserError("Invalid BPR segment")
        
        self.remittance_advice = RemittanceAdvice(
            transaction_id="",
            payer_name="",
            payer_id="",
            payee_name="",
            payee_npi="",
            payment_method=segment[2],
            payment_amount=Decimal(segment[2]),
            payment_date=datetime.strptime(segment[16], '%Y%m%d'),
            claims=[]
        )

    def _process_trn_segment(self, segment: List[str]) -> None:
        """Process the TRN (Reassociation Trace Number) segment."""
        if len(segment) < 3:
            return
        if self.remittance_advice:
            self.remittance_advice.transaction_id = segment[2]

    def _process_n1_segment(self, segment: List[str]) -> None:
        """Process the N1 (Name) segment."""
        if len(segment) < 4:
            return
        if segment[1] == 'PR':  # Payer
            self.remittance_advice.payer_name = segment[2]
            if len(segment) > 4:
                self.remittance_advice.payer_id = segment[4]
        elif segment[1] == 'PE':  # Payee
            self.remittance_advice.payee_name = segment[2]
            if len(segment) > 4:
                self.remittance_advice.payee_npi = segment[4]

    def _process_clp_segment(self, segment: List[str]) -> None:
        """Process the CLP (Claim Payment Information) segment."""
        if len(segment) < 7:
            raise RemittanceAdviceParserError("Invalid CLP segment")
        
        self._finalize_current_claim()  # Finalize previous claim if exists
        
        self.current_claim = ClaimPayment(
            claim_id=segment[1],
            patient_name="",
            charge_amount=Decimal(segment[3]),
            payment_amount=Decimal(segment[4]),
            patient_responsibility=Decimal(segment[5]),
            service_date=datetime.now(),  # Placeholder, will be updated later
            claim_status=self._get_claim_status(segment[2]),
            adjustment_reasons=[]
        )

    def _process_nm1_segment(self, segment: List[str]) -> None:
        """Process the NM1 (Individual or Organizational Name) segment."""
        if len(segment) < 4:
            return
        if segment[1] == 'QC':  # Patient
            self.current_claim.patient_name = f"{segment[3]} {segment[4]}".strip()

    def _process_dtm_segment(self, segment: List[str]) -> None:
        """Process the DTM (Date or Time or Period) segment."""
        if len(segment) < 3:
            return
        if segment[1] == '232':  # Service Date
            self.current_claim.service_date = datetime.strptime(segment[2], '%Y%m%d')

    def _process_cas_segment(self, segment: List[str]) -> None:
        """Process the CAS (Claims Adjustment) segment."""
        if len(segment) < 4:
            return
        adjustment = {
            "group_code": segment[1],
            "reason_code": segment[2],
            "amount": Decimal(segment[3])
        }
        self.current_claim.adjustment_reasons.append(adjustment)

    def _finalize_current_claim(self) -> None:
        """Finalize the current claim and add it to the remittance advice."""
        if self.current_claim and self.remittance_advice:
            self.remittance_advice.claims.append(self.current_claim)
            self.current_claim = None

    @staticmethod
    def _get_claim_status(code: str) -> str:
        """Get the claim status description for a given code."""
        statuses = {
            "1": "Processed as Primary",
            "2": "Processed as Secondary",
            "3": "Processed as Tertiary",
            "4": "Denied",
            "19": "Processed as Primary, Forwarded to Additional Payer(s)",
            "20": "Processed as Secondary, Forwarded to Additional Payer(s)",
            "21": "Processed as Tertiary, Forwarded to Additional Payer(s)",
            "22": "Reversal of Previous Payment",
            "23": "Not Our Claim, Forwarded to Additional Payer(s)",
            "25": "Predetermination Pricing Only - No Payment",
        }
        return statuses.get(code, "Unknown Status")

    def __repr__(self) -> str:
        """Provide a string representation of the parser state."""
        if self.remittance_advice:
            return (f"RemittanceAdviceParser(transaction_id={self.remittance_advice.transaction_id}, "
                    f"payment_amount={self.remittance_advice.payment_amount}, "
                    f"claim_count={len(self.remittance_advice.claims)})")
        return "RemittanceAdviceParser(No remittance advice parsed)"