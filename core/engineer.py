from typing import Dict, Any
from planner.dispatcher import route_task

def engineer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generates code using the 3-Step Sliding Window payload."""
    memory = state["memory"]
    dynamic_payload = memory.build_dynamic_payload()
    
    ledger_rules = "\n".join([f"- {rule}" for rule in memory.reflexion_ledger])
    reflexion_block = f"PERMANENT LESSONS / HEURISTICS:\n{ledger_rules}\n\n" if ledger_rules else ""

    if len(state['errors']) >= 2 and state['errors'][-1] == state['errors'][-2]:
        pattern_breaker = "WARNING: You made the exact same error twice. DO NOT repeat your previous approach. Change your logic completely."
    else:
        pattern_breaker = ""

    prompt = (
        f"{reflexion_block}"
        f"PLAN:\n{state['plan']}\n\n"
        f"{dynamic_payload}\n"
        f"{pattern_breaker}\n"
        "Write the required code to fulfill the plan. Output ONLY executable code enclosed in standard markdown tags (e.g., ```python or ```c)."
    )
    
    code_output = route_task("heavy-reasoning-model", prompt)
    
    state['draft_code'] = code_output
    state['status'] = 'evaluating'
    return state