from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.ivr.schemas import IVRAction, IVRProviderEvent


class IVRProvider(ABC):
    """
    Abstract Protocol defining telephony provider adapter capabilities.
    Isolates core IVR business logic and state machine from provider-specific formats (Twiml, Exotel XML, etc.).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier, e.g. 'mock', 'exotel'."""
        pass

    @abstractmethod
    def normalize_digit(self, raw_input: str) -> str:
        """Normalizes keypad input to standard DTMF: '0'-'9' or '#'."""
        pass

    @abstractmethod
    def validate_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        """Validates incoming provider signature or auth header."""
        pass

    @abstractmethod
    def parse_incoming_event(self, payload: Dict[str, Any]) -> IVRProviderEvent:
        """Parses provider-specific webhook into normalized IVRProviderEvent."""
        pass

    @abstractmethod
    def render_response(self, actions: List[IVRAction]) -> Any:
        """Renders internal IVR actions into provider response (e.g. JSON or XML)."""
        pass
