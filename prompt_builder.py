"""
Prompt construction module for Gemini PDF analysis.

This module handles building structured prompts that instruct Gemini
to return JSON-formatted responses with specific fields.
"""

from typing import List


def build_analysis_prompt(user_prompt: str, column_names: List[str]) -> str:
    """
    Construct the full prompt for Gemini by combining user instructions
    with JSON output formatting requirements.

    Args:
        user_prompt: The user's analysis instructions
        column_names: List of column names (excluding "Document Name")
                     that should be returned in the JSON response

    Returns:
        Complete prompt string to send to Gemini
    """
    # Filter out "Document Name" as it's auto-populated
    output_columns = [col for col in column_names if col.lower() != "document name"]

    if not output_columns:
        # If no custom columns defined, just return the user prompt
        return user_prompt

    column_list = ", ".join(f'"{col}"' for col in output_columns)

    structured_instruction = f"""

Based on your analysis, return your findings as a JSON object with exactly these keys: {column_list}

Each value should be a string. If information for a field is not found, use "N/A".

Return ONLY the JSON object, no additional text or markdown formatting."""

    return user_prompt + structured_instruction


def get_default_prompt() -> str:
    """
    Return a default example prompt for users to start with.

    Returns:
        Default analysis prompt template
    """
    return """Analyze this document and extract the following information with high accuracy.

Focus on:
- Key facts and data points
- Important dates and deadlines
- Named entities (people, organizations, locations)
- Document type and purpose

Be precise and only extract information that is explicitly stated in the document."""
