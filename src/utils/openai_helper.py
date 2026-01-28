"""
OpenAI Vision API Helper for screenshot analysis
Supports GPT-4o and GPT-4o-mini models with vision capabilities
"""
import base64
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL


class OpenAIHelper:
    """Helper class for OpenAI Vision API (GPT-5-mini, GPT-5.2, GPT-5.2-pro)"""

    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = OPENAI_MODEL):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key
            model: Model name (gpt-5-mini, gpt-5.2, gpt-5.2-pro)
        """
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. "
                "Get your key at https://platform.openai.com/api-keys "
                "and add it to .env file"
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _encode_image(self, image_path: Path) -> str:
        """
        Encode image to base64 string

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_screenshot(
        self,
        image_path: Path,
        prompt: str,
        max_tokens: int = 8192,  # Increased for GPT-5-mini reasoning tokens
        temperature: float = 0.3
    ) -> str:
        """
        Analyze a screenshot with OpenAI Vision models

        Args:
            image_path: Path to screenshot
            prompt: Analysis prompt
            max_tokens: Maximum tokens in response (reasoning + output)
            temperature: Sampling temperature (0.0-2.0, not supported by gpt-5-mini)

        Returns:
            Analysis text from the model
        """
        # Encode image to base64
        base64_image = self._encode_image(image_path)

        # Create message with image and prompt
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        # Call OpenAI API
        # Note: GPT-5-mini only supports default temperature (1.0)
        api_params = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
        }

        # Only add temperature for models that support it (not gpt-5-mini)
        if "gpt-5-mini" not in self.model.lower():
            api_params["temperature"] = temperature

        response = self.client.chat.completions.create(**api_params)

        message = response.choices[0].message
        content = message.content

        # Debug: Check if content is empty or if there's a refusal
        if hasattr(message, 'refusal') and message.refusal:
            raise ValueError(f"OpenAI refused the request: {message.refusal}")

        if not content:
            print(f"\n[DEBUG] Empty response from OpenAI")
            print(f"Model: {self.model}")
            print(f"Response object: {response}")
            print(f"Message: {message}")
            raise ValueError(f"Empty response from OpenAI API. Model: {self.model}")

        return content

    def analyze_visual_heuristics(
        self,
        image_path: Path,
        heuristics: List[str],
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze screenshot against Nielsen's heuristics

        Args:
            image_path: Path to screenshot
            heuristics: List of Nielsen's heuristics to check
            custom_prompt: Optional custom prompt (overrides default)

        Returns:
            Dictionary with analysis results and issues found
        """
        if custom_prompt:
            prompt = custom_prompt
        else:
            # Default prompt for heuristic evaluation
            heuristics_list = "\n".join([f"{i+1}. {h}" for i, h in enumerate(heuristics)])

            prompt = f"""You are a UX expert analyzing a website screenshot for usability issues.

The screenshot has a coordinate grid overlay (A, B, C... horizontally, 1, 2, 3... vertically).

Evaluate this interface against Nielsen's 10 Usability Heuristics:
{heuristics_list}

For each visible issue, provide:
1. Which heuristic is violated (use exact name from the list)
2. Grid location: single cell (e.g., "C4") or range (e.g., "B3-C4" for multi-cell elements)
3. Specific description of the problem (reference UI elements by position or text)
4. Severity (Critical/High/Medium/Low)
5. Suggested fix

IMPORTANT:
- Only report issues you can clearly see in the screenshot
- Use grid coordinates for precise location (single cell "C4" or range "B3-C4")
- If an element spans multiple cells, use range notation (e.g., "A1-D2")

Respond in JSON format:
{{
  "issues": [
    {{
      "heuristic": "exact heuristic name",
      "description": "specific issue description",
      "severity": "Critical|High|Medium|Low",
      "location": "grid coordinates (e.g., 'C4' or 'B3-C4')",
      "recommendation": "specific fix suggestion"
    }}
  ],
  "summary": "overall assessment (2-3 sentences)",
  "positive_aspects": ["good UX elements found"],
  "priority_fixes": ["most critical issues to fix first"]
}}"""

        # Get analysis from GPT-4o
        response_text = self.analyze_screenshot(
            image_path,
            prompt,
            temperature=0.3
        )

        # Return raw response as dict
        return {
            "raw_response": response_text,
            "model": self.model,
            "image_path": str(image_path)
        }

    def analyze_with_persona(
        self,
        image_path: Path,
        persona_prompt: str,
        task_description: str,
        max_tokens: int = 1500
    ) -> str:
        """
        Analyze screenshot from a specific persona's perspective

        Args:
            image_path: Path to screenshot
            persona_prompt: Persona description and context
            task_description: What the persona is trying to do
            max_tokens: Maximum response length

        Returns:
            Analysis from persona's perspective
        """
        prompt = f"""{persona_prompt}

Task: {task_description}

Looking at this interface, describe:
1. First impression (what catches your eye?)
2. Can you easily complete your task? Why or why not?
3. What confuses you or slows you down?
4. What works well?
5. On a scale 1-10, how easy is this interface to use? Why?

Be honest and specific based on what you see in the screenshot."""

        return self.analyze_screenshot(
            image_path,
            prompt,
            max_tokens=max_tokens,
            temperature=0.7  # Higher temperature for more natural persona voice
        )


# Example usage and testing
if __name__ == "__main__":
    import sys

    # Check if API key is set
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
        print("❌ Error: OPENAI_API_KEY not set in .env file")
        print("   Get your key at: https://platform.openai.com/api-keys")
        sys.exit(1)

    print(f"✓ OpenAI API Key configured")
    print(f"✓ Model: {OPENAI_MODEL}")
    print(f"✓ OpenAIHelper ready to use")

    # Test with a screenshot if provided
    if len(sys.argv) > 1:
        test_image = Path(sys.argv[1])
        if test_image.exists():
            print(f"\nTesting with image: {test_image}")
            helper = OpenAIHelper()
            result = helper.analyze_screenshot(
                test_image,
                "Describe what you see in this screenshot in 2-3 sentences."
            )
            print(f"\nResult: {result}")
        else:
            print(f"❌ Image not found: {test_image}")
