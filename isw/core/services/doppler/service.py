from typing import Any, Dict, Optional

import requests


class DopplerServiceError(Exception):
    """Raised for Doppler API errors."""


class DopplerService:
    """
    Minimal wrapper around Doppler's REST API.

    Core feature implemented:
      • create_service_token(project, config, name, ...)
    """

    def __init__(self, api_token: str) -> None:
        self.base_url = "https://api.doppler.com/v3"
        self.api_token = api_token
        if not self.api_token:
            raise DopplerServiceError(
                "A Doppler API token is required. Pass it to DopplerService(api_token=...) or set DOPPLER_API_TOKEN."
            )

        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_token}",
        }

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic POST wrapper with uniform error handling.
        """
        url = f"{self.base_url}{path}"
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            msg = f"Doppler API request failed: {e.response.status_code}"
            try:
                details = e.response.json()
                msg += f" – {details.get('message', details)}"
            except ValueError:
                msg += f" – {e.response.text}"
            raise DopplerServiceError(msg) from e
        except requests.exceptions.RequestException as e:
            raise DopplerServiceError(f"Network error talking to Doppler: {e}") from e

        return resp.json()

    def create_service_token(
        self,
        project: str,
        config: str,
        name: str,
        expire_at: Optional[int] = None,
        access: str = "read",
    ) -> Dict[str, Any]:
        """
        Create a Doppler *service token* bound to <project>/<config>.

        Args:
            project:   Project slug (e.g., 'my-api')
            config:    Config slug  (e.g., 'prod' or 'dev')
            name:      Friendly name for the token
            expire_at: Optional unix timestamp for expiry (leave None for non-expiring)
            access:    'read' (default) or other future values

        Returns:
            Dict with the full token object, e.g.:
            {
              "name": "ci-prod-2025-06",
              "access": "read",
              "token": "dp.st.prod.xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
              "created_at": "2025-06-26T22:25:18Z",
              ...
            }
        """
        payload = {
            "project": project,
            "config": config,
            "name": name,
            "access": access,
        }
        if expire_at:
            payload["expire_at"] = expire_at

        path = "/configs/config/tokens"
        return self._post(path, payload)
