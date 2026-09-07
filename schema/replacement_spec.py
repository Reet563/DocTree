from pydantic import BaseModel, Field
from typing import List

class TextReplacement(BaseModel):
    old_text: str = Field(description="The exact text string found in the original DOCX that needs to be replaced.")
    new_text: str = Field(description="The new text string that should take its place.")

class ReplacementMap(BaseModel):
    replacements: List[TextReplacement] = Field(description="A list of all text replacements to perform on the template.")
