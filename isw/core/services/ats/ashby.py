import hashlib
import hmac
from datetime import datetime
from typing import Optional

import requests

from ....shared.config import config
from ....shared.logging.logger import logger
from ...errors import ServiceException


class AshbyService:
    """
    Service for interacting with the Ashby API.
    """

    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None):
        conf = config()
        self._auth = (api_key or conf.ashby_api_key, "")
        self._secret = secret or conf.ashby_secret

    def add_note_to_candidate(self, candidate_id: str, note: str, notify: bool = False) -> bool:
        """
        Add a note to a candidate.

        Args:
            candidate_id: The ID of the candidate to add the note to.
            note: The note to add to the candidate.
            notify: Whether to send a notification to the candidate.

        Returns:
            True if the note was added successfully, False otherwise.
        """
        try:
            data = {
                "candidateId": candidate_id,
                "createdAt": datetime.now().isoformat(),
                "note": {
                    "value": note,
                    "type": "text/html",
                },
                "sendNotifications": notify,
            }

            self._send_request("candidate.createNote", data)
            return True
        except Exception as e:
            logger.error(f"Failed to add note to candidate: {e}")
            return False

    def generate_candidate_profile_url(self, candidate_id: str, application_id: str) -> str:
        """
        Assemble remote URL for a candidate's profile.

        Args:
            candidate_id: The ID of the candidate to generate a profile URL for.
            application_id: The ID of the application to generate a profile URL for.

        Returns:
            The remote URL for a candidate's profile.
        """
        return f"https://app.ashbyhq.com/candidate-searches/new/right-side/candidates/{candidate_id}/applications/{application_id}/feed"

    def get_application(self, application_id: str) -> dict | None:
        """
        Retrieve an application by its ID.

        Args:
            application_id: The ID of the application to retrieve.

        Returns:
            The application, or None if the application was not found.
        """
        entity_query = {
            "applicationId": application_id,
        }

        return self._send_request_for_single_entity(
            endpoint="application.info",
            entity_query=entity_query,
            entity_error_code="application_not_found",
        )

    def get_candidate(self, candidate_id: str) -> dict | None:
        """
        Retrieve a candidate by their ID.

        Args:
            candidate_id: The ID of the candidate to retrieve.

        Returns:
            The candidate, or None if the candidate was not found.
        """
        entity_query = {
            "id": candidate_id,
        }

        return self._send_request_for_single_entity(
            endpoint="candidate.info",
            entity_query=entity_query,
            entity_error_code="candidate_not_found",
        )

    def get_file_info(self, file_handle: str) -> dict | None:
        """
        Retrieve the url of a file associated with a candidate

        Args:
            file_handle: The handle of the file to retrieve.

        Returns:
            The url of the file, or None if the file was not found.
        """
        entity_query = {
            "fileHandle": file_handle,
        }

        return self._send_request_for_single_entity(
            endpoint="file.info",
            entity_query=entity_query,
            entity_error_code="file_not_found",
        )

    def validate_webhook_signature(self, signature: str, body: bytes) -> bool:
        """
        Validate the signature of a request.

        Args:
            signature: The signature to validate.
            body: The raw body of the request.

        Returns:
            True if the signature is valid, False otherwise.
        """
        try:
            hash_object = hmac.new(key=self._secret.encode(), msg=body, digestmod=hashlib.sha256)
            return hmac.compare_digest(f"sha256={hash_object.hexdigest()}", signature)
        except Exception:
            return False

    def _get_endpoint(self, endpoint: str) -> str:
        """
        Get the endpoint for the Ashby API.

        Args:
            endpoint: The endpoint to send the request to.

        Returns:
            The endpoint for the Ashby API.
        """
        return f"https://api.ashbyhq.com/{endpoint}"

    def _has_intended_error(self, response: dict, error_code: str) -> bool:
        """
        Check if the response has an intended error.

        Args:
            response: The response from the Ashby API.
            error_code: The error code to check for.

        Returns:
            True if the response has an intended error, False otherwise.
        """
        try:
            return not response.get("success") and response.get("errorInfo", {}).get("code") == error_code
        except Exception:
            return False

    def _send_request(self, endpoint: str, json: dict) -> dict:
        """
        Send a request to the Ashby API.

        Args:
            endpoint: The endpoint to send the request to.
            json: The JSON body to send to the endpoint.

        Returns:
            The response from the Ashby API.
        """
        try:
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
            }

            response = requests.post(
                self._get_endpoint(endpoint),
                auth=self._auth,
                headers=headers,
                json=json,
            )

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ashby API request failed with response: {e}")
            raise ServiceException("ATS provider failed to complete request") from e
        except Exception as e:
            logger.error(f"Ashby API request failed with unknown error: {e}")
            raise ServiceException("ATS provider encountered an unknown error") from e

    def _send_request_for_single_entity(self, endpoint: str, entity_query: dict, entity_error_code: str) -> dict | None:
        """
        Send a request to the Ashby API for a single entity.
        If the request fails with an intended error, return None.
        Otherwise, return the results of the request.

        Args:
            endpoint: The endpoint to send the request to.
            entity_query: The query to send to the endpoint.
            entity_error_code: The error code to check for.

        Returns:
            The results of the request, or None if the request failed with an intended error.
        """
        response = self._send_request(endpoint, entity_query)
        if self._has_intended_error(response, entity_error_code):
            return None

        return response.get("results", {})
