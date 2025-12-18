This is the fundamental LLM/Transformer mechanism, broken down from the bottom up.

1. What is implemented
	- SDPA (single-head)
	- causal / padding masks
	- PyTorch-compatible semantics
	- Multi-Head Attention

2. What is intentionally NOT implemented
	- FlashAttention kernels
	- fused ops
	- performance optimizations

3. API contracts
	- is_causal -> attn_mask must be None
	- attn_mask: True = allowed
	- dropout behavior
	