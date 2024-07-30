from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class EligibilityRequest:
    subscriber_id: str
    subscriber_name: str
    subscriber_dob: datetime
    provider_npi: str
    service_type_code: str

@dataclass
class EligibilityResponse:
    is_eligible: bool
    subscriber_id: str
    subscriber_name: str
    plan_status: str
    plan_description: Optional[str]
    coverage_level: Optional[str]
    service_type_code: str
    service_type_name: str
    copay: Optional[float]
    coinsurance: Optional[float]
    deductible: Optional[float]

class EligibilityCheckerError(Exception):
    """Custom exception for EligibilityChecker errors."""

class EligibilityChecker:
    """
    A robust checker for handling X12 270 (Eligibility Request) and 271 (Eligibility Response) transactions.
    
    This class provides methods to create eligibility requests and process eligibility responses
    for dental insurance verification.
    """

    SEGMENT_TERMINATOR = '~'
    ELEMENT_SEPARATOR = '*'
    
    def __init__(self):
        self.request: Optional[EligibilityRequest] = None
        self.response: Optional[EligibilityResponse] = None

    def create_270_request(self, request: EligibilityRequest) -> str:
        """
        Create an X12 270 (Eligibility Request) transaction.
        
        Args:
            request (EligibilityRequest): The eligibility request details.
        
        Returns:
            str: The X12 270 transaction as a string.
        
        Raises:
            EligibilityCheckerError: If the request creation fails.
        """
        try:
            self.request = request
            segments = []
            segments.extend(self._create_header_segments())
            segments.extend(self._create_2000_loop())
            segments.extend(self._create_trailer_segments(len(segments) + 2))  # +2 for SE and IEA
            return self.SEGMENT_TERMINATOR.join(segments) + self.SEGMENT_TERMINATOR
        except Exception as e:
            raise EligibilityCheckerError(f"Failed to create 270 request: {str(e)}") from e

    def process_271_response(self, x12_content: str) -> EligibilityResponse:
        """
        Process an X12 271 (Eligibility Response) transaction.
        
        Args:
            x12_content (str): The X12 271 transaction as a string.
        
        Returns:
            EligibilityResponse: The processed eligibility response.
        
        Raises:
            EligibilityCheckerError: If the response processing fails.
        """
        try:
            segments = self._split_into_segments(x12_content)
            self.response = self._process_segments(segments)
            return self.response
        except Exception as e:
            raise EligibilityCheckerError(f"Failed to process 271 response: {str(e)}") from e

    def _split_into_segments(self, x12_content: str) -> List[List[str]]:
        """Split the X12 content into individual segments and elements."""
        segments = x12_content.strip().split(self.SEGMENT_TERMINATOR)
        return [seg.split(self.ELEMENT_SEPARATOR) for seg in segments if seg]

    def _create_header_segments(self) -> List[str]:
        """Create the header segments for the 270 request."""
        isa = f"ISA*00*          *00*          *ZZ*REQUESTOR      *ZZ*PAYER          *{datetime.now():%y%m%d}*{datetime.now():%H%M}*^*00501*000000001*0*P*:"
        gs = f"GS*HS*REQUESTOR*PAYER*{datetime.now():%Y%m%d}*{datetime.now():%H%M%S}*1*X*005010X279A1"
        st = "ST*270*0001*005010X279A1"
        bht = f"BHT*0022*13*10001234*{datetime.now():%Y%m%d}*{datetime.now():%H%M}"
        return [isa, gs, st, bht]

    def _create_2000_loop(self) -> List[str]:
        """Create the 2000 loop segments for the 270 request."""
        segments = []
        segments.append("HL*1**20*1")
        segments.append("NM1*PR*2*PAYER NAME*****PI*PAYER ID")
        segments.append("HL*2*1*21*1")
        segments.append(f"NM1*1P*2*PROVIDER NAME*****XX*{self.request.provider_npi}")
        segments.append("HL*3*2*22*1")
        segments.append(f"NM1*IL*1*{self.request.subscriber_name}*****MI*{self.request.subscriber_id}")
        segments.append(f"DMG*D8*{self.request.subscriber_dob:%Y%m%d}")
        segments.append(f"EQ*{self.request.service_type_code}")
        return segments

    def _create_trailer_segments(self, segment_count: int) -> List[str]:
        """Create the trailer segments for the 270 request."""
        se = f"SE*{segment_count}*0001"
        ge = "GE*1*1"
        iea = "IEA*1*000000001"
        return [se, ge, iea]

    def _process_segments(self, segments: List[List[str]]) -> EligibilityResponse:
        """Process the 271 response segments and extract eligibility information."""
        response = EligibilityResponse(
            is_eligible=False,
            subscriber_id="",
            subscriber_name="",
            plan_status="",
            plan_description=None,
            coverage_level=None,
            service_type_code="",
            service_type_name="",
            copay=None,
            coinsurance=None,
            deductible=None
        )

        for segment in segments:
            if segment[0] == "NM1" and segment[1] == "IL":
                response.subscriber_id = segment[9]
                response.subscriber_name = f"{segment[3]} {segment[4]}".strip()
            elif segment[0] == "EB":
                self._process_eb_segment(segment, response)

        return response

    def _process_eb_segment(self, segment: List[str], response: EligibilityResponse) -> None:
        """Process the EB (Eligibility or Benefit Information) segment."""
        if segment[1] == "1":
            response.is_eligible = True
            response.plan_status = "Active"
        elif segment[1] in ("6", "7", "8"):
            response.plan_status = "Inactive"

        if len(segment) > 2:
            response.service_type_code = segment[2]
            response.service_type_name = self._get_service_type_name(segment[2])

        for i in range(3, len(segment)):
            if segment[i] == "FAM":
                response.coverage_level = "Family"
            elif segment[i] == "IND":
                response.coverage_level = "Individual"
            elif segment[i].startswith("PLA"):
                response.plan_description = segment[i][3:]
            elif segment[i] == "C1":
                response.copay = float(segment[i+1]) if i+1 < len(segment) else None
            elif segment[i] == "C2":
                response.coinsurance = float(segment[i+1]) if i+1 < len(segment) else None
            elif segment[i] == "D":
                response.deductible = float(segment[i+1]) if i+1 < len(segment) else None

    @staticmethod
    def _get_service_type_name(code: str) -> str:
        """Get the service type name for a given code."""
        service_types = {
            "1": "Medical Care",
            "35": "Dental Care",
            "48": "Hospital - Inpatient",
            "50": "Hospital - Outpatient",
            "86": "Emergency Services",
            "98": "Professional (Physician) Visit - Office",
            "AL": "Vision (Optometry)",
            "MH": "Mental Health",
            "UC": "Urgent Care",
        }
        return service_types.get(code, "Unknown Service Type")

    def __repr__(self) -> str:
        """Provide a string representation of the checker state."""
        status = "No request/response"
        if self.response:
            status = f"Response processed (Eligible: {self.response.is_eligible})"
        elif self.request:
            status = "Request created, awaiting response"
        return f"EligibilityChecker({status})"