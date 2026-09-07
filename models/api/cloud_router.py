import os
import requests
from typing import Optional

class CloudRouter:
    """
    Routes requests to cloud models through either OpenRouter or Groq.
    """
    def __init__(self, provider: str = "openrouter", model: str = "meta-llama/llama-3.1-70b-instruct", mock: bool = False):
        self.mock = mock
        self.provider = provider.lower()
        self.model = model
        
        if not self.mock:
            if self.provider == "groq":
                from groq import Groq
                self.groq_client = Groq()
            elif self.provider == "openrouter":
                self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
                if not self.openrouter_api_key:
                    print("WARNING: OPENROUTER_API_KEY not found in environment.")

    def generate(self, system_prompt: str, user_prompt: str, images: Optional[list] = None) -> str:
        if self.mock:
            return '{"document_type": "Quiz", "metadata": {}, "page": {"size": "A4", "orientation": "portrait", "margins": {"top_mm": 20.0, "bottom_mm": 20.0, "left_mm": 20.0, "right_mm": 20.0}}, "theme": {"body": {"font_family": "Arial", "size_pt": 11.0, "bold": false, "italic": false, "underline": false, "color": {"hex_code": "#000000"}}, "h1": {"font_family": "Arial", "size_pt": 16.0, "bold": true, "italic": false, "underline": false, "color": {"hex_code": "#000000"}}, "h2": {"font_family": "Arial", "size_pt": 14.0, "bold": true, "italic": false, "underline": false, "color": {"hex_code": "#000000"}}, "h3": {"font_family": "Arial", "size_pt": 12.0, "bold": true, "italic": false, "underline": false, "color": {"hex_code": "#000000"}}, "answer_key": {"font_family": "Arial", "size_pt": 11.0, "bold": false, "italic": true, "underline": false, "color": {"hex_code": "#FF0000"}}}, "sections": [{"title": "Math Pop Quiz", "page_break_before": false, "elements": [{"element_type": "text", "content": "Instructions: Read the questions carefully and select the best answer.", "is_heading": false, "heading_level": 1, "alignment": "left", "style_override": null}, {"element_type": "text", "content": "1. What is 5 + 7?", "is_heading": false, "heading_level": 1, "alignment": "left", "style_override": null}, {"element_type": "list", "list_type": "lettered", "items": [{"content": "10"}, {"content": "11"}, {"content": "12"}, {"content": "13"}]}]}]}'
            
        if self.provider == "groq":
            return self._generate_groq(system_prompt, user_prompt) # Groq (at least the models we use) doesn't support our vision payload yet
        elif self.provider == "openrouter":
            return self._generate_openrouter(system_prompt, user_prompt, images)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _generate_groq(self, system_prompt: str, user_prompt: str) -> str:
        # Groq uses different model IDs than OpenRouter
        groq_model = "openai/gpt-oss-120b"
        if "8b" in self.model.lower():
            groq_model = "openai/gpt-oss-20b"
            
        completion = self.groq_client.chat.completions.create(
            model=groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=3000,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
        )
        return completion.choices[0].message.content

    def _generate_openrouter(self, system_prompt: str, user_prompt: str, images: Optional[list] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "DocTree",
            "Content-Type": "application/json"
        }
        
        user_content = [{"type": "text", "text": user_prompt}]
        if images:
            for b64 in images:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                })
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
