import torch
from attention import SelfAttentionBlock  # Assuming your file is named attention.py
import matplotlib.pyplot as plt
from einops import rearrange
import math

# Set random seed for reproducibility
torch.manual_seed(0)

# Create a dummy input tensor
x = torch.randn(2, 5, 16)  # (batch_size, seq_len, d_embed)

# Create the SelfAttentionBlock instance
attn = SelfAttentionBlock(n_heads=4, d_embed=16)

# Run the forward pass
output = attn(x, causal_mask=False)

# Print output shape
print("Final output shape:", output.shape)

# Modify the forward method temporarily to return both output and weights.
def forward_debug(self, x: torch.Tensor, causal_mask=False):
    inp = self.in_proj(x)
    q, k, v = inp.chunk(3, dim=-1)
    q = rearrange(q, "bs sl (nh dh) -> bs nh sl dh", nh=self.n_heads)
    k = rearrange(k, "bs sl (nh dh) -> bs nh sl dh", nh=self.n_heads)
    v = rearrange(v, "bs sl (nh dh) -> bs nh sl dh", nh=self.n_heads)
    kT = rearrange(k, "bs nh sl dh -> bs nh dh sl")
    weight = q @ kT
    if causal_mask:
        mask = torch.ones_like(weight, dtype=torch.bool).triu(1)
        weight.masked_fill_(mask, -torch.inf)
    weight /= math.sqrt(self.dim_head)
    weight = torch.softmax(weight, dim=-1)
    output = weight @ v
    output = rearrange(output, "bs nh sl dh -> bs sl (nh dh)")
    return self.out_proj(output), weight

# Bind the debug method to your instance (monkey patching)
attn.forward = forward_debug.__get__(attn, SelfAttentionBlock)

# Run the model with causal masking
output, weights = attn(x, causal_mask=True)
print("Weights shape:", weights.shape)  # Should be (2, 4, 4, 4)

# Plot the attention weights of the first head and first batch item
plt.imshow(weights[0, 0].detach().cpu(), cmap="viridis")
plt.colorbar()
plt.title("Attention Weights for Head 0, Batch 0 (causal_mask=True)")
plt.xlabel("Key Positions")
plt.ylabel("Query Positions")
plt.show()
