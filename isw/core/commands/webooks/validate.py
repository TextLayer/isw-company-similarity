from ...errors import ValidationException
from ...services.ats import ATSService
from ...services.evals import EvalsService
from ..base import WriteCommand


class ValidateWebhookCommand(WriteCommand):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def validate(self):
        if self.provider_name not in ["ashby", "langfuse"]:
            raise ValidationException(f"Invalid provider name: {self.provider_name}")

    def execute(self):
        """Abstract command for validating webhooks in different services"""
        provider_name = self.__dict__.get("provider_name")

        if provider_name == "ashby":
            return ATSService().validate_webhook_signature(
                body=self.__dict__.get("body"),
                signature=self.__dict__.get("signature"),
            )
        if provider_name == "langfuse":
            return EvalsService(provider_name).validate_webhook_signature(
                body=self.__dict__.get("body"),
                signature=self.__dict__.get("signature"),
            )
