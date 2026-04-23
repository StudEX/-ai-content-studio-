"""Context Compressor — compresses prompts and context to reduce token usage.

Implements automatic conversation history summarization when approaching context limits.
Uses Ollama for local summarization (free) or Claude for higher quality summaries.
"""

import os
from typing import Optional, List, Dict
import httpx

# Model context windows (tokens)
MODEL_CONTEXT_WINDOWS = {
    # Claude models
    "claude-opus-4-6": 200000,
    "claude-sonnet-4-6": 200000,
    "claude-haiku-4-5": 200000,
    "claude-opus-4-5": 200000,
    "claude-sonnet-4-5": 200000,
    # Ollama models
    "llama3.1:8b": 8192,
    "llama3.1:70b": 8192,
    "llama3.2:3b": 8192,
    "mistral:7b": 8192,
    "gemma2:9b": 8192,
    "qwen2.5:7b": 32768,
    "deepseek-r1:8b": 32768,
}

# Compression threshold — start compressing at 70% of context window
COMPRESSION_THRESHOLD = 0.70

# Keep this many recent messages uncompressed
RECENT_MESSAGES_KEEP = 10


class ContextCompressor:
    """Compresses conversation history to stay within context limits.

    Features:
    - Automatic summarization when conversation exceeds 70% of context window
    - Local Ollama summarization (free) or Claude (higher quality)
    - Token counting and compression savings tracking
    - Preserves last N messages uncompressed for context freshness
    """

    def __init__(self, ollama_url: Optional[str] = None):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.compression_count = 0
        self.tokens_saved = 0

    # Stop words for simple text compression
    STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                  "have", "has", "had", "do", "does", "did", "will", "would", "could",
                  "should", "may", "might", "shall", "can", "to", "of", "in", "for",
                  "on", "with", "at", "by", "from", "as", "into", "through", "during",
                  "before", "after", "above", "below", "between", "under", "again",
                  "further", "then", "once", "here", "there", "when", "where", "why",
                  "how", "all", "each", "every", "both", "few", "more", "most", "other",
                  "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
                  "too", "very", "just", "because", "but", "and", "if", "while",
                  "that", "this", "it"}

    def compress(self, text: str, context: Optional[dict] = None) -> str:
        """Compress input text and merge with context.

        Simple line-by-line compression that removes stop words.
        Use compress_history() for full conversation summarization.
        """
        lines = text.strip().split("\n")
        compressed_lines = [self._compress_line(line) for line in lines if line.strip()]
        base = "\n".join(compressed_lines)

        if context:
            ctx_str = " | ".join(f"{k}={v}" for k, v in context.items() if v)
            return f"[CTX: {ctx_str}] {base}"
        return base

    def _compress_line(self, line: str) -> str:
        words = line.split()
        if len(words) <= 8:
            return line
        # Keep meaningful words for longer lines
        compressed = [w for w in words if w.lower() not in self.STOP_WORDS or w[0].isupper()]
        return " ".join(compressed) if compressed else line

    def estimate_tokens(self, text: str) -> int:
        """Rough token count — ~4 chars per token."""
        return max(1, len(text) // 4)

    def count_tokens(self, messages: List[Dict], model: str) -> int:
        """Count tokens in a message list.

        Uses Ollama's tokenizer if available, falls back to character-based estimation.
        """
        try:
            # Try Ollama tokenizer endpoint (if available)
            import httpx
            text = " ".join(m.get("content", "") for m in messages if isinstance(m.get("content"), str))
            # Ollama doesn't expose tokenizer via API — use estimation
            return self.estimate_tokens(text)
        except Exception:
            return self.estimate_tokens(" ".join(m.get("content", "") for m in messages))

    async def compress_history(
        self,
        messages: List[Dict],
        model: str = "claude-sonnet-4-6",
        use_claude: bool = False,
    ) -> tuple[List[Dict], Dict]:
        """Compress conversation history when approaching context limits.

        Args:
            messages: List of conversation messages (role + content dicts)
            model: Model name to get context window for
            use_claude: Use Claude for summarization (higher quality) vs Ollama (free)

        Returns:
            tuple: (compressed_messages, stats_dict)
        """
        context_window = MODEL_CONTEXT_WINDOWS.get(model, 200000)
        threshold = int(context_window * COMPRESSION_THRESHOLD)

        # Count current tokens
        current_tokens = self.count_tokens(messages, model)

        # Check if compression needed
        if current_tokens <= threshold:
            return messages, {
                "compressed": False,
                "reason": f"Under threshold ({current_tokens:,} / {threshold:,} tokens)",
                "tokens_used": current_tokens,
                "threshold": threshold,
            }

        # Need to compress — keep last N messages fresh
        old_messages = messages[:-RECENT_MESSAGES_KEEP]
        recent_messages = messages[-RECENT_MESSAGES_KEEP:]

        # Summarize old messages
        if use_claude:
            summary = await self._summarize_with_claude(old_messages)
        else:
            summary = await self._summarize_with_ollama(old_messages)

        # Build compressed history
        system_message = {
            "role": "system",
            "content": f"[COMPRESSED CONTEXT]: {summary}\n\n[Note: Earlier conversation summarized above. Last {RECENT_MESSAGES_KEEP} messages preserved in full.]"
        }

        compressed_messages = [system_message] + recent_messages
        compressed_tokens = self.count_tokens(compressed_messages, model)
        tokens_saved = current_tokens - compressed_tokens

        self.compression_count += 1
        self.tokens_saved += tokens_saved

        return compressed_messages, {
            "compressed": True,
            "original_tokens": current_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": tokens_saved,
            "compression_ratio": round(1 - (compressed_tokens / current_tokens), 2),
            "messages_removed": len(old_messages),
            "messages_kept": len(recent_messages),
        }

    async def _summarize_with_ollama(self, messages: List[Dict]) -> str:
        """Summarize conversation using local Ollama model (free)."""
        # Build conversation text
        conversation = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in messages
            if m.get("role") and m.get("content")
        )

        prompt = (
            "Summarize this conversation in 3-5 sentences. "
            "Capture key decisions, conclusions, and context. "
            "Be concise but preserve important details.\n\n"
            f"Conversation:\n{conversation[:8000]}"  # Truncate to avoid overflow
        )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "llama3.1:8b",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3, "max_tokens": 500},
                    }
                )
                resp.raise_for_status()
                result = resp.json()
                return result.get("response", "[Summary unavailable]")
        except Exception as e:
            return f"[Ollama summarization failed: {str(e)}]"

    async def _summarize_with_claude(self, messages: List[Dict]) -> str:
        """Summarize conversation using Claude (higher quality)."""
        from services.claude_service import ClaudeService

        claude = ClaudeService()
        if not claude.configured:
            return await self._summarize_with_ollama(messages)

        # Build conversation text
        conversation = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in messages
            if m.get("role") and m.get("content")
        )

        system_prompt = (
            "You are a conversation summarizer. Summarize the conversation in 3-5 sentences. "
            "Capture key decisions, conclusions, facts learned, and important context. "
            "Be concise but preserve critical details needed for continuation."
        )

        prompt = f"Conversation to summarize:\n{conversation[:15000]}"  # Larger limit for Claude

        try:
            response, _ = await claude.generate(
                system=system_prompt,
                prompt=prompt,
                model="claude-haiku-4-5",  # Use cheaper model for summarization
                max_tokens=500,
                use_thinking=False,
            )
            return response
        except Exception:
            return await self._summarize_with_ollama(messages)

    def get_stats(self) -> Dict:
        """Get compression statistics."""
        return {
            "compression_count": self.compression_count,
            "total_tokens_saved": self.tokens_saved,
            "estimated_cost_savings_usd": round(self.tokens_saved / 1_000_000 * 3.0, 4),  # Sonnet rate
        }
