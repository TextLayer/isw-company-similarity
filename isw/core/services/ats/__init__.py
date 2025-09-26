from .ashby import AshbyService

# note: alias in case we add other ats providers in the future
ATSService = AshbyService

__all__ = ["ATSService"]
