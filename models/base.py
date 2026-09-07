from typing import Protocol

class DocumentGenerator(Protocol):
    """
    Base protocol for any model/provider that generates document JSON.
    """
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...
