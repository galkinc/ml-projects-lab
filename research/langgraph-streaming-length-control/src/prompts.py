"""
Centralized prompt templates for the benchmark.
"""

BASE_SYSTEM_PROMPT = """Always respond in exactly 8 to 12 words. Be concise.

Examples:
- User: "What is Python?"
  Response: "Programming language for computing and data science applications."
- User: "Explain AWS."
  Response: "Cloud computing platform providing storage compute networking services."

Respond in 8-12 words ONLY."""

RETRY_PROMPT_TEMPLATE = """The response above contains {word_count} words.
It failed the length constraint.
It is a negative example.
Rewrite it to be exactly 8-12 words. Focus on the core meaning.
Stop after 12 words."""
