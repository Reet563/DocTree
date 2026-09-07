from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Union

# --- Typography & Style ---
class ColorSpec(BaseModel):
    hex_code: str = Field(description="Hex color code, e.g., #000000")

class FontStyle(BaseModel):
    font_family: Optional[str] = None
    size_pt: Optional[float] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: Optional[ColorSpec] = None

class TypographyTheme(BaseModel):
    body: FontStyle = Field(default_factory=FontStyle)
    h1: FontStyle = Field(default_factory=FontStyle)
    h2: FontStyle = Field(default_factory=FontStyle)
    h3: FontStyle = Field(default_factory=FontStyle)
    answer_key: FontStyle = Field(default_factory=FontStyle)

# --- Page Layout ---
class Margins(BaseModel):
    top_mm: float
    bottom_mm: float
    left_mm: float
    right_mm: float

class PageSettings(BaseModel):
    size: Literal["A4", "Letter", "Legal"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margins: Margins
    column_count: int = 1
    line_spacing_pt: float = 12.0
    has_page_border: bool = False

# --- Content Elements ---
class TextBlock(BaseModel):
    element_type: Literal["text"] = "text"
    content: str
    is_heading: bool = False
    heading_level: int = 1
    alignment: Literal["left", "center", "right", "justify"] = "left"
    style_override: Optional[FontStyle] = None

class ListItem(BaseModel):
    content: str

class ListBlock(BaseModel):
    element_type: Literal["list"] = "list"
    list_type: Literal["bullet", "numbered", "lettered"] = "bullet"
    items: List[ListItem]

class SpacerBlock(BaseModel):
    element_type: Literal["spacer"] = "spacer"
    space_lines: int = 1
    has_lines: bool = False

class ImageElement(BaseModel):
    element_type: Literal["image"] = "image"
    source_path: str
    width_mm: Optional[float] = None
    caption: Optional[str] = None

class TableCell(BaseModel):
    content: str
    is_header: bool = False
    col_span: int = 1

class TableBlock(BaseModel):
    element_type: Literal["table"] = "table"
    rows: List[List[TableCell]]
    has_borders: bool = True
    column_widths_mm: Optional[List[float]] = None
    alignment: Literal["left", "center", "right"] = "left"

DocumentElement = Union[TextBlock, ListBlock, TableBlock, SpacerBlock, ImageElement]

# --- Structural Hierarchy ---
class Section(BaseModel):
    title: Optional[str] = None
    elements: List[DocumentElement]
    page_break_before: bool = False

# --- Master Specification ---
class DocumentSpec(BaseModel):
    document_type: str = Field(description="e.g., question_paper, resume, report")
    metadata: dict = Field(default_factory=dict)
    
    page: PageSettings
    theme: TypographyTheme
    
    sections: List[Section]
