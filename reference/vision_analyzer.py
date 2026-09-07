import os
import base64
import json
import pymupdf
from typing import Tuple, List

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema.reference_spec import ReferenceSpec
from models.base import DocumentGenerator

class VisionAnalyzer:
    def __init__(self, file_paths: List[str], llm: DocumentGenerator):
        self.file_paths = file_paths
        self.llm = llm

    def _pdf_to_base64_images(self, path: str, max_pages: int = 3) -> List[str]:
        b64_images = []
        try:
            doc = pymupdf.open(path)
            for i in range(min(len(doc), max_pages)):
                page = doc[i]
                # Render to pixmap (PNG)
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                b64_images.append(b64)
        except Exception as e:
            print(f"Error converting PDF {path} to images: {e}")
        return b64_images

    def _img_to_base64(self, path: str) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def analyze(self) -> ReferenceSpec:
        """
        Uses a Vision LLM to extract exactly how the document looks.
        """
        self.all_b64_images = []
        for path in self.file_paths:
            ext = path.split('.')[-1].lower()
            if ext == "pdf":
                # Only take the first 3 pages of each PDF to avoid massive payloads
                self.all_b64_images.extend(self._pdf_to_base64_images(path, max_pages=3))
            elif ext in ["png", "jpg", "jpeg"]:
                self.all_b64_images.append(self._img_to_base64(path))
                
        if not self.all_b64_images:
            return None

        system_prompt = """You are an expert Document Template Analyzer.
Your job is to look at the provided images of a document and output a STRICT JSON object representing its visual style.
Do NOT output any conversational text. ONLY output valid JSON.

You must output JSON exactly matching this schema:
{
    "page_width_mm": float,
    "page_height_mm": float,
    "margins": {"top_mm": float, "bottom_mm": float, "left_mm": float, "right_mm": float},
    "body_font": {"font_family": string, "size_pt": float},
    "heading_fonts": [{"font_family": string, "size_pt": float}],
    "colors": [string],
    "line_spacing_pt": float,
    "primary_alignment": "left|center|right|justify",
    "column_count": int,
    "has_columns": bool
}

RULES:
1. Estimate page size (A4 is 210x297).
2. Estimate margins (standard is 25.4mm for 1 inch).
3. Estimate fonts (e.g. Arial, Times New Roman).
4. Colors must be hex codes.
"""
        user_prompt = "Analyze these document pages and return the ReferenceSpec JSON."
        
        try:
            json_str = self.llm.generate(system_prompt, user_prompt, images=self.all_b64_images)
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "{" in json_str and "}" in json_str:
                json_str = json_str[json_str.find("{"):json_str.rfind("}")+1]
                
            data = json.loads(json_str)
            return ReferenceSpec(**data)
        except Exception as e:
            print(f"VisionAnalyzer Error: {e}")
            return None
