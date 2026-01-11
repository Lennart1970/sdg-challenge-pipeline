"""
LLM client module with support for OpenAI Responses API and structured outputs
"""

import json
import logging
from typing import Protocol, Optional, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """Protocol for LLM clients"""
    def complete(self, prompt: str, model: str, system_prompt: Optional[str] = None) -> str:
        """
        Complete a prompt and return the response as a string
        
        Args:
            prompt: User prompt
            model: Model identifier
            system_prompt: Optional system prompt
            
        Returns:
            Response text (may be JSON string for structured outputs)
        """
        ...


class OpenAIResponsesLLM:
    """
    OpenAI Responses API client returning strict JSON using Structured Outputs.
    
    This client uses OpenAI's Responses API with JSON Schema validation
    to guarantee well-formed JSON output that matches the provided schema.
    
    Key features:
    - Guaranteed JSON shape (no "almost-json" failures)
    - Schema validation enforced by API
    - No brands/SKUs by design (enforced in schema and prompt)
    - Easy database writes (already validated)
    """
    
    def __init__(self, schema: Dict[str, Any], schema_name: str = "structured_output"):
        """
        Initialize OpenAI Responses client with structured output schema
        
        Args:
            schema: JSON Schema for structured output validation
            schema_name: Name for the schema (used in API call)
        """
        self.client = OpenAI()
        self.schema = schema
        self.schema_name = schema_name
        logger.info(f"Initialized OpenAI Responses LLM with schema: {schema_name}")
    
    def complete(self, prompt: str, model: str, system_prompt: Optional[str] = None) -> str:
        """
        Complete a prompt using OpenAI Responses API with structured outputs
        
        Args:
            prompt: User prompt
            model: Model identifier (e.g., 'gpt-4.1-mini')
            system_prompt: Optional system prompt (defaults to generic constraint-driven agent)
            
        Returns:
            JSON string conforming to the schema
        """
        if system_prompt is None:
            system_prompt = "You are a constraint-driven technology discovery agent."
        
        logger.info(f"Calling OpenAI Responses API with model: {model}")
        
        try:
            # Call Responses API with structured outputs
            # IMPORTANT: We pass the schema to the API, so we don't rely on "please output JSON" prompting
            resp = self.client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": self.schema_name,
                        "strict": True,
                        "schema": self.schema,
                    }
                },
            )
            
            # This is the JSON string that conforms to the schema
            output_text = resp.output_text
            
            # Validate it's actually JSON (should always be true with structured outputs)
            try:
                json.loads(output_text)
                logger.info("Successfully received and validated structured JSON output")
            except json.JSONDecodeError as e:
                logger.error(f"Received invalid JSON from API (this should not happen): {e}")
                raise
            
            return output_text
            
        except Exception as e:
            logger.error(f"Error calling OpenAI Responses API: {e}")
            raise


class OpenAIChatLLM:
    """
    Standard OpenAI Chat Completions API client (for non-structured outputs)
    
    This is a fallback for cases where structured outputs are not needed,
    or for compatibility with the existing challenge extraction workflow.
    """
    
    def __init__(self):
        """Initialize OpenAI Chat client"""
        self.client = OpenAI()
        logger.info("Initialized OpenAI Chat LLM")
    
    def complete(self, prompt: str, model: str, system_prompt: Optional[str] = None) -> str:
        """
        Complete a prompt using OpenAI Chat Completions API
        
        Args:
            prompt: User prompt
            model: Model identifier
            system_prompt: Optional system prompt
            
        Returns:
            Response text
        """
        if system_prompt is None:
            system_prompt = "You are a helpful assistant."
        
        logger.info(f"Calling OpenAI Chat API with model: {model}")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            output_text = response.choices[0].message.content
            logger.info("Successfully received chat completion")
            
            return output_text
            
        except Exception as e:
            logger.error(f"Error calling OpenAI Chat API: {e}")
            raise


def build_llm_client(
    provider: str,
    schema: Optional[Dict[str, Any]] = None,
    schema_name: Optional[str] = None
) -> LLMClient:
    """
    Factory function to build LLM client based on provider
    
    Args:
        provider: LLM provider name ('openai_responses', 'openai_chat')
        schema: Optional JSON schema for structured outputs
        schema_name: Optional name for the schema
        
    Returns:
        LLM client instance
        
    Raises:
        ValueError: If provider is unknown or schema is missing for structured outputs
    """
    provider = (provider or "").lower().strip()
    
    if provider in ("openai", "openai_responses"):
        if not schema:
            raise ValueError("OpenAI Responses provider requires a JSON schema.")
        return OpenAIResponsesLLM(
            schema=schema,
            schema_name=schema_name or "structured_output"
        )
    
    elif provider == "openai_chat":
        return OpenAIChatLLM()
    
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
