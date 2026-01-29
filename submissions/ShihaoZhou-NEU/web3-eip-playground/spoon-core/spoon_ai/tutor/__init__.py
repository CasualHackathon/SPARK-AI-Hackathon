"""
Tutor service package.

Provides a minimal FastAPI app and EIP-1559 derived calculations
for demo-friendly "operation -> feedback -> explanation" flows.
"""

from .service import app, compute_eip1559_derived

__all__ = ["app", "compute_eip1559_derived"]

