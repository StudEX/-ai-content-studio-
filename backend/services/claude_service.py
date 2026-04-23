"""Claude AI Service — powers all 9 Naledi agents via Anthropic API.

Implements latest best practices:
- Adaptive thinking for Claude 4.6+ models
- Effort parameter for cost-quality control
- Streaming for long responses
- Prompt caching for repeated contexts
- Structured outputs with Pydantic
- Token counting and cost estimation in ZAR
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, TypeVar, Type, TYPE_CHECKING
from pydantic import BaseModel

# For type hints to avoid circular imports
if TYPE_CHECKING:
    from services.context_compressor import ContextCompressor

from anthropic import Anthropic, APIError, RateLimitError, AuthenticationError, BadRequestError
from anthropic.types import Message, TextBlock, ThinkingBlock, ToolUseBlock

SAST = timezone(timedelta(hours=2))
USD_TO_ZAR = 18.50

# Number of recent messages to keep uncompressed in chat_with_history
RECENT_MESSAGES_KEEP = 10

# Model pricing per 1M tokens (USD)
MODEL_PRICING = {
    "claude-opus-4-6": {"input": 5.0, "output": 25.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 1.0, "output": 5.0},
    "claude-opus-4-5": {"input": 5.0, "output": 25.0},
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
}

# Context windows per model
CONTEXT_WINDOWS = {
    "claude-opus-4-6": 200000,
    "claude-sonnet-4-6": 200000,
    "claude-haiku-4-5": 200000,
    "claude-opus-4-5": 200000,
    "claude-sonnet-4-5": 200000,
}


class TokenUsage:
    """Track token usage and calculate costs."""

    def __init__(self, input_tokens: int = 0, output_tokens: int = 0,
                 cache_read_tokens: int = 0, cache_write_tokens: int = 0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_read_tokens = cache_read_tokens
        self.cache_write_tokens = cache_write_tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def cost_estimate(self, model: str) -> Dict[str, float]:
        """Calculate cost estimate in ZAR."""
        pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})

        # Cache tokens cost differently
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        cache_read_cost = (self.cache_read_tokens / 1_000_000) * pricing["input"] * 0.1  # 10% of base
        cache_write_cost = (self.cache_write_tokens / 1_000_000) * pricing["input"] * 1.25  # 1.25x for 5min TTL

        total_usd = input_cost + output_cost + cache_read_cost + cache_write_cost
        return {
            "input_zar": round(input_cost * USD_TO_ZAR, 4),
            "output_zar": round(output_cost * USD_TO_ZAR, 4),
            "cache_read_zar": round(cache_read_cost * USD_TO_ZAR, 4),
            "cache_write_zar": round(cache_write_cost * USD_TO_ZAR, 4),
            "total_zar": round(total_usd * USD_TO_ZAR, 4),
        }


class ClaudeService:
    """Claude AI service with latest API features."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client = Anthropic(api_key=api_key) if api_key else None
        self.default_model = "claude-opus-4-6"  # Default to most capable
        self._session_tokens = 0

    @property
    def configured(self) -> bool:
        return self.client is not None

    @property
    def session_tokens(self) -> int:
        return self._session_tokens

    def reset_session_tokens(self):
        self._session_tokens = 0

    async def count_tokens(self, messages: List[Dict], system: str = "", model: str | None = None) -> int:
        """Count tokens in a message list before making API call."""
        if not self.client:
            return 0

        try:
            response = self.client.messages.count_tokens(
                model=model or self.default_model,
                messages=messages,
                system=system if system else None,
            )
            return response.input_tokens
        except Exception:
            # Fallback: rough estimate (~4 chars per token)
            text = system + " ".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))
            return len(text) // 4

    async def generate(
        self,
        system: str,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 16000,
        use_thinking: bool = True,
        effort: str = "high",  # low | medium | high | max
        use_cache: bool = True,
    ) -> tuple[str, TokenUsage]:
        """Generate response from Claude with adaptive thinking.

        Returns:
            tuple: (response_text, token_usage)
        """
        if not self.client:
            return "[Claude not configured — set ANTHROPIC_API_KEY]", TokenUsage()

        target_model = model or self.default_model

        # Build request params
        params: Dict[str, Any] = {
            "model": target_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        # System prompt with caching
        if system:
            if use_cache:
                params["system"] = [{
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }]
            else:
                params["system"] = system

        # Adaptive thinking for 4.6+ models
        if use_thinking and any(v in target_model for v in ["opus-4", "sonnet-4"]):
            params["thinking"] = {"type": "adaptive"}
            params["output_config"] = {"effort": effort}

        try:
            response = self.client.messages.create(**params)

            # Extract text and thinking
            text_parts = []
            thinking_parts = []

            for block in response.content:
                if isinstance(block, TextBlock):
                    text_parts.append(block.text)
                elif isinstance(block, ThinkingBlock):
                    thinking_parts.append(block.thinking)

            # Track tokens
            usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cache_read_tokens=getattr(response.usage, 'cache_read_input_tokens', 0),
                cache_write_tokens=getattr(response.usage, 'cache_creation_input_tokens', 0),
            )
            self._session_tokens += usage.total_tokens

            # Include thinking in response if present
            full_response = "\n".join(text_parts)
            if thinking_parts:
                full_response = f"[Thinking: {' '.join(thinking_parts)[:500]}...]\n\n{full_response}"

            return full_response, usage

        except AuthenticationError:
            return "[Authentication failed — check ANTHROPIC_API_KEY]", TokenUsage()
        except RateLimitError as e:
            retry_after = e.response.headers.get("retry-after", "60")
            return f"[Rate limited — retry after {retry_after}s]", TokenUsage()
        except BadRequestError as e:
            return f"[Bad request: {e.message}]", TokenUsage()
        except APIError as e:
            return f"[API error {e.status_code}: {e.message}]", TokenUsage()

    async def generate_streaming(
        self,
        system: str,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 64000,
        use_thinking: bool = True,
        effort: str = "high",
    ):
        """Stream response from Claude. Yields (event_type, data) tuples.

        Yields:
            tuple: (event_type, data) where event_type is 'text', 'thinking', 'usage', or 'done'
        """
        if not self.client:
            yield "error", "[Claude not configured]"
            return

        target_model = model or self.default_model

        params: Dict[str, Any] = {
            "model": target_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system:
            params["system"] = [{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }]

        if use_thinking and any(v in target_model for v in ["opus-4", "sonnet-4"]):
            params["thinking"] = {"type": "adaptive"}
            params["output_config"] = {"effort": effort}

        try:
            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield "text", text

                final_message = stream.get_final_message()

                # Yield usage
                usage = TokenUsage(
                    input_tokens=final_message.usage.input_tokens,
                    output_tokens=final_message.usage.output_tokens,
                    cache_read_tokens=getattr(final_message.usage, 'cache_read_input_tokens', 0),
                    cache_write_tokens=getattr(final_message.usage, 'cache_creation_input_tokens', 0),
                )
                self._session_tokens += usage.total_tokens
                yield "usage", usage

        except Exception as e:
            yield "error", str(e)

    async def generate_structured(
        self,
        system: str,
        prompt: str,
        output_schema: Type[BaseModel],
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> tuple[BaseModel | None, TokenUsage, str | None]:
        """Generate structured output validated against Pydantic schema.

        Returns:
            tuple: (parsed_output or None, token_usage, error_message or None)
        """
        if not self.client:
            return None, TokenUsage(), "[Claude not configured]"

        try:
            # Build schema from Pydantic model
            schema = output_schema.model_json_schema()

            params: Dict[str, Any] = {
                "model": model or self.default_model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "output_config": {
                    "format": {
                        "type": "json_schema",
                        "schema": schema,
                    }
                },
            }

            if system:
                params["system"] = system

            response = self.client.messages.create(**params)

            # Extract and parse JSON
            text_block = next((b for b in response.content if isinstance(b, TextBlock)), None)
            if not text_block:
                return None, TokenUsage(), "No text response from Claude"

            try:
                data = json.loads(text_block.text)
                parsed = output_schema.model_validate(data)

                usage = TokenUsage(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
                self._session_tokens += usage.total_tokens

                return parsed, usage, None

            except json.JSONDecodeError as e:
                return None, TokenUsage(), f"Failed to parse JSON: {e}"
            except Exception as e:
                return None, TokenUsage(), f"Schema validation failed: {e}"

        except Exception as e:
            return None, TokenUsage(), str(e)

    async def chat_with_history(
        self,
        messages: List[Dict],
        system: str = "",
        model: str | None = None,
        max_tokens: int = 16000,
        use_thinking: bool = True,
        auto_compress: bool = True,
    ) -> tuple[str, List[Dict], TokenUsage, Dict | None]:
        """Chat with conversation history. Returns (response, updated_history, usage, compression_stats).

        Messages should alternate user/assistant roles.

        Args:
            messages: Conversation history (user/assistant alternating)
            system: System prompt
            model: Model to use (defaults to claude-opus-4-6)
            max_tokens: Max tokens for response
            use_thinking: Enable adaptive thinking for 4.6+ models
            auto_compress: Automatically compress history when > 70% context window

        Returns:
            tuple: (response_text, updated_history, token_usage, compression_stats or None)
        """
        if not self.client:
            return "", messages, TokenUsage(), None

        target_model = model or self.default_model

        # Auto-compress if enabled and conversation is long
        compression_stats = None
        if auto_compress and len(messages) > RECENT_MESSAGES_KEEP:
            from services.context_compressor import ContextCompressor
            compressor = ContextCompressor()
            messages, compression_stats = await compressor.compress_history(
                messages, model=target_model, use_claude=False
            )

        params: Dict[str, Any] = {
            "model": target_model,
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system:
            params["system"] = [{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }]

        if use_thinking and any(v in target_model for v in ["opus-4", "sonnet-4"]):
            params["thinking"] = {"type": "adaptive"}

        try:
            response = self.client.messages.create(**params)

            # Extract assistant response
            text_parts = [b.text for b in response.content if isinstance(b, TextBlock)]
            assistant_text = "\n".join(text_parts)

            # Add to history
            updated_history = messages + [{"role": "assistant", "content": assistant_text}]

            usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            self._session_tokens += usage.total_tokens

            return assistant_text, updated_history, usage, compression_stats

        except Exception as e:
            return "", messages, TokenUsage(), compression_stats

    def get_model_info(self, model: str | None = None) -> Dict[str, Any]:
        """Get model info including context window and pricing."""
        target_model = model or self.default_model

        return {
            "model": target_model,
            "context_window": CONTEXT_WINDOWS.get(target_model, 200000),
            "pricing_usd": MODEL_PRICING.get(target_model, {"input": 0, "output": 0}),
            "pricing_zar": {
                "input_per_1m": round(MODEL_PRICING.get(target_model, {"input": 0})["input"] * USD_TO_ZAR, 2),
                "output_per_1m": round(MODEL_PRICING.get(target_model, {"output": 0})["output"] * USD_TO_ZAR, 2),
            },
        }

    async def get_session_report(self) -> Dict[str, Any]:
        """Get current session token usage and cost report."""
        usage = TokenUsage()  # Would track cumulative if we stored per-type
        usage.input_tokens = self._session_tokens // 2
        usage.output_tokens = self._session_tokens // 2

        costs = usage.cost_estimate(self.default_model)

        return {
            "total_tokens": self._session_tokens,
            "costs_zar": costs,
            "time_sast": datetime.now(SAST).isoformat(),
        }
