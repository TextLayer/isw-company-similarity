from datetime import UTC, datetime

from ....shared.config import config
from ...schemas.onboarding_schemas import invite_request_schema
from ...services.jwt.jwt import JWTService
from ...services.mail.service import MailService
from ...services.mail.types import EmailRecipients
from ..base import WriteCommand


class InviteCommand(WriteCommand):
    def __init__(self, email: str, expires_in_hours: int):
        self.email = email
        self.expires_in_hours = expires_in_hours

    def validate(self):
        invite_request_schema.load(self.__dict__)

    def execute(self) -> dict:
        token = JWTService().generate_token(
            subject="onboarding_invite",
            data={"email": self.email},
            expires_in=self.__convert_hours_to_seconds(self.expires_in_hours),
        )

        MailService().send_email(
            recipients=EmailRecipients(to=[self.email]),
            subject="TextLayer - Onboarding Invite",
            template_name="onboarding",
            template_data={
                "onboarding_url": f"{config().client_url}/onboarding?token={token}",
                "year": datetime.now(UTC).year,
            },
        )

        return {"status": "success", "expires_in_hours": self.expires_in_hours}

    def __convert_hours_to_seconds(self, hours: int) -> int:
        one_hour_in_seconds = 3600
        return hours * one_hour_in_seconds
