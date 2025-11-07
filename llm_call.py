"""
LLM API calls with structured JSON responses using Gemini.
"""

import google.generativeai as genai
from typing import Dict, Any, Type
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """Client for making structured LLM calls"""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        Initialize LLM client.

        Args:
            model_name: Name of the Gemini model to use
        """
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[BaseModel],
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> BaseModel:
        """
        Generate structured response using JSON schema validation.

        Args:
            system_prompt: System instruction for the model
            user_prompt: User query/task
            response_schema: Pydantic model for response validation
            temperature: Model temperature (0.0-1.0)
            max_retries: Maximum retry attempts on failure

        Returns:
            Validated Pydantic model instance

        Raises:
            ValueError: If response doesn't match schema after retries
        """
        # Combine system and user prompts
        full_prompt = f"""{system_prompt}

{user_prompt}

CRITICAL: Return ONLY valid JSON that matches this exact schema:
{response_schema.model_json_schema()}

Do not include any markdown formatting, code blocks, or additional text.
Return pure JSON only."""

        for attempt in range(max_retries):
            try:
                # Configure generation with max output tokens
                # Note: response_schema causes "$defs" error with Pydantic schemas
                generation_config = genai.GenerationConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                    max_output_tokens=8192,  # Maximum for gemini-2.0-flash
                )

                # Generate response
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings={
                        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                    }
                )

                response_text = response.text.strip()

                # Clean response (remove markdown if present)
                response_text = self._clean_json_response(response_text)

                # Parse and validate with Pydantic
                validated_response = response_schema.model_validate_json(response_text)

                return validated_response

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"    Attempt {attempt + 1} failed: {e}")
                    print(f"    Retrying...")
                    continue
                else:
                    print(f"    ERROR: Failed after {max_retries} attempts")
                    print(f"    Last error: {e}")
                    raise ValueError(f"Failed to generate valid response: {e}")

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate JSON response without strict schema validation.
        Useful for simple responses like variation arrays.

        Args:
            system_prompt: System instruction
            user_prompt: User query
            temperature: Model temperature
            max_retries: Maximum retry attempts

        Returns:
            Parsed JSON dictionary
        """
        full_prompt = f"""{system_prompt}

{user_prompt}

CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no additional text."""

        for attempt in range(max_retries):
            try:
                generation_config = genai.GenerationConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                    #max_output_tokens=32768,
                )

                response = self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )

                response_text = response.text.strip()
                response_text = self._clean_json_response(response_text)

                # Parse JSON
                json_response = json.loads(response_text)
                return json_response

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"    Attempt {attempt + 1} failed: {e}")
                    continue
                else:
                    raise ValueError(f"Failed to generate valid JSON: {e}")

    def _clean_json_response(self, text: str) -> str:
        """
        Clean JSON response by removing markdown formatting and fixing escape sequences.

        Args:
            text: Raw response text

        Returns:
            Cleaned JSON string
        """
        import re

        # Remove markdown code blocks
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]

        # Remove control characters except newline and tab
        # Keep \n (\x0a) and \t (\x09) as they're valid in JSON strings
        text = re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', ' ', text)

        # Try to parse and let JSON handle the rest
        # If it fails, it will be caught by the validation layer

        return text.strip()


# Singleton instance
_llm_client = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
