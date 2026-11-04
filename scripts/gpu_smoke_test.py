"""Confirm torch (scvi-tools) and jax (scib-metrics) both see the GPU in the same environment."""
import jax, torch
print("torch", torch.__version__, "cuda_available", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
print("jax", jax.__version__, "devices", jax.devices())
x = torch.randn(2000, 2000, device="cuda"); print("torch matmul ok", float((x @ x).sum()) != 0)
import jax.numpy as jnp; print("jax matmul ok", float(jnp.ones((2000, 2000)).sum()))
