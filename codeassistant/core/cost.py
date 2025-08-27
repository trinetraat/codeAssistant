from typing import Dict
from .config import PRICING

def estimate_cost_usd(model: str, usage_obj) -> float:
    if not usage_obj: return 0.0
    input_t = getattr(usage_obj, "input_tokens", 0) or 0
    output_t = getattr(usage_obj, "output_tokens", 0) or 0
    rate = PRICING.get(model, {"input": 0.0, "output": 0.0})
    return (input_t/1_000_000)*rate["input"] + (output_t/1_000_000)*rate["output"]