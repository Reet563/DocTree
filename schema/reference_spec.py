from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedMargins(BaseModel):
    top_mm: float
    bottom_mm: float
    left_mm: float
    right_mm: float

class ExtractedFont(BaseModel):
    font_family: str
    size_pt: float

class ReferenceSpec(BaseModel):
    # Page layout
    page_width_mm: float
    page_height_mm: float
    margins: ExtractedMargins
    
    # Typography deduced from frequencies
    body_font: ExtractedFont
    heading_fonts: List[ExtractedFont] = Field(description="Heading fonts found, sorted largest to smallest")
    
    # Extracted colors (hex strings)
    colors: List[str]
    
    # Layout and structure hints
    has_columns: bool = False
    column_count: int = Field(default=1, description="Number of text columns detected")
    line_spacing_pt: float = Field(default=12.0, description="Average line spacing in points")
    primary_alignment: str = Field(default="left", description="left, center, or justify")
