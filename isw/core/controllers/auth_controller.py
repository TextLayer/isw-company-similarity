from ..commands.auth.refresh_session_token import RefreshSessionTokenCommand
from .base import Controller


class AuthController(Controller):
    def refresh_session_token(self, *args, **kwargs) -> str:
        return self.executor.execute_write(RefreshSessionTokenCommand(*args, **kwargs))
