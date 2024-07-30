import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
import logging

@dataclass
class APIResponse:
    success: bool
    status_code: int
    data: Any
    message: str

class X12APIWrapperError(Exception):
    """Custom exception for X12APIWrapper errors."""

class X12APIWrapper:
    """
    A robust API wrapper for X12 EDI clearinghouses or payers.
    
    This class provides methods to interact with X12 EDI APIs, including
    submitting claims, checking claim status, and verifying eligibility.
    """
    
    def __init__(self, base_url: str, api_key: str, api_secret: Optional[str] = None):
        """
        Initialize the X12APIWrapper.
        
        Args:
            base_url (str): The base URL of the X12 API.
            api_key (str): The API key for authentication.
            api_secret (Optional[str]): The API secret for authentication, if required.
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.logger = self._setup_logger()

    def submit_claim(self, claim_data: Dict[str, Any]) -> APIResponse:
        """
        Submit a claim to the X12 API.
        
        Args:
            claim_data (Dict[str, Any]): The claim data in a dictionary format.
        
        Returns:
            APIResponse: The response from the API.
        
        Raises:
            X12APIWrapperError: If the API request fails.
        """
        endpoint = f"{self.base_url}/claims"
        return self._make_request('POST', endpoint, json=claim_data)

    def check_claim_status(self, claim_id: str) -> APIResponse:
        """
        Check the status of a claim.
        
        Args:
            claim_id (str): The ID of the claim to check.
        
        Returns:
            APIResponse: The response from the API.
        
        Raises:
            X12APIWrapperError: If the API request fails.
        """
        endpoint = f"{self.base_url}/claims/{claim_id}/status"
        return self._make_request('GET', endpoint)

    def verify_eligibility(self, eligibility_data: Dict[str, Any]) -> APIResponse:
        """
        Verify eligibility for a patient.
        
        Args:
            eligibility_data (Dict[str, Any]): The eligibility data in a dictionary format.
        
        Returns:
            APIResponse: The response from the API.
        
        Raises:
            X12APIWrapperError: If the API request fails.
        """
        endpoint = f"{self.base_url}/eligibility"
        return self._make_request('POST', endpoint, json=eligibility_data)

    def get_remittance_advice(self, remittance_id: str) -> APIResponse:
        """
        Retrieve a remittance advice.
        
        Args:
            remittance_id (str): The ID of the remittance advice to retrieve.
        
        Returns:
            APIResponse: The response from the API.
        
        Raises:
            X12APIWrapperError: If the API request fails.
        """
        endpoint = f"{self.base_url}/remittance/{remittance_id}"
        return self._make_request('GET', endpoint)

    def _make_request(self, method: str, url: str, **kwargs) -> APIResponse:
        """Make an HTTP request to the API."""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return APIResponse(
                success=True,
                status_code=response.status_code,
                data=response.json(),
                message="Request successful"
            )
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            return APIResponse(
                success=False,
                status_code=getattr(e.response, 'status_code', None),
                data=None,
                message=str(e)
            )

    def _setup_logger(self) -> logging.Logger:
        """Set up a logger for the X12APIWrapper."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def __repr__(self) -> str:
        """Provide a string representation of the X12APIWrapper."""
        return f"X12APIWrapper(base_url='{self.base_url}')"