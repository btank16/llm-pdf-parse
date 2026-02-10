"""
Gemini API client module for PDF analysis.

Handles PDF upload, content generation, and response parsing
with retry logic and error handling.
"""

import json
import os
import re
import time
import tempfile
import pathlib
from typing import Dict, Any, Optional, Tuple
from google import genai


class GeminiPDFAnalyzer:
    """Client for analyzing PDFs using Google's Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-pro-preview",
        max_retries: int = 2,
        api_delay: float = 1.0
    ):
        """
        Initialize the Gemini PDF analyzer.

        Args:
            api_key: Google Gemini API key
            model: Model identifier (default: gemini-3-pro-preview)
            max_retries: Maximum number of retry attempts for failed requests
            api_delay: Delay in seconds between API calls
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.api_delay = api_delay

    def analyze_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        prompt: str
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Analyze a PDF file using Gemini API.

        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename (for error reporting)
            prompt: Analysis prompt to send to Gemini

        Returns:
            Tuple of (success, result_dict, error_message)
            - success: True if analysis succeeded
            - result_dict: Parsed JSON response or {"Raw Response": text} on parse failure
            - error_message: Error description if success is False, None otherwise
        """
        uploaded_file = None
        temp_file_path = None

        try:
            # Create temporary file for upload
            temp_file_path = self._write_temp_pdf(pdf_bytes, filename)

            # Upload to Gemini Files API
            uploaded_file = self._upload_file(temp_file_path)

            # Generate content with retries
            response_text = self._generate_content_with_retry(uploaded_file, prompt)

            # Parse JSON response
            result_dict = self._parse_json_response(response_text)

            # Add delay before next request
            time.sleep(self.api_delay)

            return True, result_dict, None

        except Exception as e:
            error_msg = f"Error analyzing {filename}: {str(e)}"
            return False, {}, error_msg

        finally:
            # Cleanup: delete uploaded file and temp file
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass  # Ignore cleanup errors

            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass  # Ignore cleanup errors

    def _write_temp_pdf(self, pdf_bytes: bytes, filename: str) -> str:
        """
        Write PDF bytes to a temporary file.

        Args:
            pdf_bytes: PDF content as bytes
            filename: Original filename (used for temp file naming)

        Returns:
            Path to temporary file
        """
        # Create temp file with .pdf extension
        suffix = ".pdf"
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix=suffix,
            delete=False
        ) as temp_file:
            temp_file.write(pdf_bytes)
            return temp_file.name

    def _upload_file(self, file_path: str):
        """
        Upload a file to Gemini Files API.

        Args:
            file_path: Path to PDF file

        Returns:
            Uploaded file object

        Raises:
            Exception: If upload fails
        """
        path = pathlib.Path(file_path)
        return self.client.files.upload(file=path)

    def _generate_content_with_retry(
        self,
        uploaded_file,
        prompt: str
    ) -> str:
        """
        Generate content from Gemini with retry logic.

        Args:
            uploaded_file: File object from Files API
            prompt: Analysis prompt

        Returns:
            Response text from Gemini

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[uploaded_file, prompt]
                )

                # Extract text from response
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'parts'):
                    return ''.join(part.text for part in response.parts if hasattr(part, 'text'))
                else:
                    raise ValueError("Unexpected response format from Gemini")

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                else:
                    raise last_exception

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON from Gemini response, handling markdown code fences.

        Args:
            response_text: Raw response text from Gemini

        Returns:
            Parsed JSON as dictionary, or {"Raw Response": text} if parsing fails
        """
        # Remove markdown code fences if present
        cleaned_text = response_text.strip()

        # Pattern: ```json ... ``` or ``` ... ```
        json_pattern = r'^```(?:json)?\s*\n(.*?)\n```$'
        match = re.match(json_pattern, cleaned_text, re.DOTALL)

        if match:
            cleaned_text = match.group(1).strip()

        # Try to parse JSON
        try:
            result = json.loads(cleaned_text)
            if isinstance(result, dict):
                return result
            else:
                # If not a dict, wrap it
                return {"Raw Response": str(result)}
        except json.JSONDecodeError:
            # If parsing fails, return raw response
            return {"Raw Response": response_text}


def validate_api_key() -> Tuple[bool, Optional[str]]:
    """
    Validate that GEMINI_API_KEY environment variable is set.

    Returns:
        Tuple of (is_valid, api_key)
    """
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return False, None

    return True, api_key
