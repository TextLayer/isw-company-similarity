from .client import ObservabilityClient
from .contexts.utils import (
    get_current_observation_id,
    get_current_trace_id,
    score_current_observation,
    score_current_trace,
    update_current_observation,
    update_current_trace,
)
from .decorators import observe
from .exporters import (
    check_exporter_availability,
    get_exporter_info,
)
from .integrations import LangchainCallbackHandler

# Global singleton instance
obs = ObservabilityClient()

flush = obs.flush
trace = obs.trace
span = obs.span
generation = obs.generation
event = obs.event
score = obs.score


__all__ = [
    # Main client
    "obs",
    "ObservabilityClient",
    # Decorator
    "observe",
    # Main functions (aliases to obs methods)
    "flush",
    "trace",
    "span",
    "generation",
    "event",
    "score",
    # Integration factories
    "LangchainCallbackHandler",
    # Context utilities
    "get_current_trace_id",
    "get_current_observation_id",
    "update_current_trace",
    "update_current_observation",
    "score_current_observation",
    "score_current_trace",
    # Exporter utilities
    "get_exporter_info",
    "check_exporter_availability",
]
