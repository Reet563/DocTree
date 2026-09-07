import os
import json
from groq import Groq

class GroqGenerator:
    def __init__(self, mock: bool = False):
        self.mock = mock
        if not self.mock:
            # Requires GROQ_API_KEY in environment
            self.client = Groq()

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Calls Groq API with JSON Mode enabled.
        """
        if self.mock:
            return '{"document_type": "Quiz", "metadata": {}, "page": {"size": "A4", "orientation": "portrait", "margins": {"top_mm": 20.0, "bottom_mm": 20.0, "left_mm": 20.0, "right_mm": 20.0}}, "theme": {"body": {"font_family": "Arial", "size_pt": 11.0, "bold": false, "italic": false, "underline": false, "color": {"hex_code": "#000000"}}, "h1": {"font_family": "Arial", "size_pt": 16.0, "bold": true, "italic": false, "underline": false, "color": {"hex_code": "#000000"}}, "h2": {"font_family": "Arial", "size_pt": 14.0, "bold": true, "italic": false, "underline": false, "color": {"hex_code": "#000000"}}, "h3": {"font_family": "Arial", "size_pt": 12.0, "bold": true, "italic": false, "underline": false, "color": {"hex_code": "#000000"}}, "answer_key": {"font_family": "Arial", "size_pt": 11.0, "bold": false, "italic": true, "underline": false, "color": {"hex_code": "#FF0000"}}}, "sections": [{"title": "Math Pop Quiz", "page_break_before": false, "elements": [{"element_type": "text", "content": "Instructions: Read the questions carefully and select the best answer.", "is_heading": false, "heading_level": 1, "alignment": "left", "style_override": null}, {"element_type": "text", "content": "1. What is 5 + 7?", "is_heading": false, "heading_level": 1, "alignment": "left", "style_override": null}, {"element_type": "list", "list_type": "lettered", "items": [{"content": "10"}, {"content": "11"}, {"content": "12"}, {"content": "13"}]}]}]}'

        completion = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=2500,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )
        
        return completion.choices[0].message.content
