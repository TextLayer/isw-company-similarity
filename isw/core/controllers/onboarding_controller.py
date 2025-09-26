from ..commands.onboarding.get_textlayer_core import GetTextlayerCoreCommand
from ..commands.onboarding.invite import InviteCommand
from ..commands.onboarding.list_textlayer_core_versions import ListTextlayerCoreVersionsCommand
from .base import Controller


class OnboardingController(Controller):
    def get_textlayer_core(self, **kwargs):
        return self.executor.execute_read(GetTextlayerCoreCommand(**kwargs))

    def list_textlayer_versions(self, **kwargs):
        return self.executor.execute_read(ListTextlayerCoreVersionsCommand(**kwargs))

    def invite(self, **kwargs):
        return self.executor.execute_write(InviteCommand(**kwargs))
