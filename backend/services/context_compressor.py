"""Context Compressor — compresses prompts and context to reduce token usage."""

from typing import Optional


class ContextCompressor:
    """Strips noise from inputs, merges context, and produces lean prompts."""

    STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                  "have", "has", "had", "do", "does", "did", "will", "would", "could",
                  "should", "may", "might", "shall", "can", "to", "of", "in", "for",
                  "on", "with", "at", "by", "from", "as", "into", "through", "during",
                  "before", "after", "above", "below", "between", "under", "again",
                  "further", "then", "once", "here", "there", "when", "where", "why",
                  "how", "all", "each", "every", "both", "few", "more", "most", "other",
                  "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
                  "too", "very", "just", "because", "but", "and", "or", "if", "while",
                  "that", "this", "it", "its"}

    def compress(self, text: str, context: Optional[dict] = None) -> str:
        """Compress input text and merge with context."""
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
