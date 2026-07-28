from typing import TypedDict, List, Dict
from planner.dispatcher import route_task
from tools.sandbox import run_python_code, run_c_code
from memory.core_memory import MemoryManager

# 1. Define the Global State Dictionary
class GraphState(TypedDict):
    task: str
    plan: str
    draft_code: str
    errors: List[str]
    iteration_count: int
    status: str  # 'planning', 'coding', 'evaluating', 'complete', or 'failed'
    memory: MemoryManager  # Added to manage token-optimized memory tiering

# Define the hard guardrail to prevent infinite loops
MAX_AGENT_TURNS = 3

# 2. Define the Nodes (Agents)
def planner_node(state: GraphState) -> GraphState:
    """Uses a heavy reasoning model to break the problem into logical steps."""
    memory: MemoryManager = state["memory"]
    
    # Register the initial task objective into memory Tier 1
    memory.set_current_state(objective=state['task'])
    
    prompt = f"Create a step-by-step engineering plan to solve this task: {state['task']}"
    plan_output = route_task("heavy-reasoning-model", prompt)
    
    # Log action to sliding window memory
    memory.log_action(
        action_desc="Planner generated execution plan",
        result_desc="Plan generated successfully"
    )
    
    state['plan'] = plan_output
    state['status'] = 'coding'
    return state


def engineer_node(state: GraphState) -> GraphState:
    """Generates code using the 3-Step Sliding Window payload instead of full history."""
    memory: MemoryManager = state["memory"]
    
    # Extract short-term dynamic payload (Tier 2 window + Tier 1 current state)
    dynamic_payload = memory.build_dynamic_payload()
    
    # Format permanent lessons learned from the ledger (Tier 3)
    ledger_rules = "\n".join([f"- {rule}" for rule in memory.reflexion_ledger])
    reflexion_block = f"PERMANENT LESSONS / HEURISTICS:\n{ledger_rules}\n\n" if ledger_rules else ""

    # Construct token-trimmed prompt (saves 70-80% compared to appending full raw error histories)
    prompt = (
        f"{reflexion_block}"
        f"PLAN:\n{state['plan']}\n\n"
        f"{dynamic_payload}\n"
        "Write the required code to fulfill the plan. Output ONLY executable code."
    )
    
    code_output = route_task("heavy-reasoning-model", prompt)
    
    state['draft_code'] = code_output
    state['status'] = 'evaluating'
    return state


def evaluator_node(state: GraphState) -> GraphState:
    """Tests code in a real execution environment and feeds trimmed state back to Memory."""
    memory: MemoryManager = state["memory"]
    state['iteration_count'] += 1
    
    # 1. Attempt deterministic sandbox execution
    if "python" in state['task'].lower() or "def " in state['draft_code']:
        execution_result = run_python_code(state['draft_code'])
    elif "gcc" in state['task'].lower() or "#include" in state['draft_code']:
        execution_result = run_c_code(state['draft_code'])
    else:
        # Fallback to LLM static analysis
        execution_result = None

    # 2. Check deterministic execution results
    if execution_result:
        if execution_result['success']:
            # Log success to sliding window and clear current error
            memory.log_action(
                action_desc="Executed draft code in E2B sandbox",
                result_desc="Success - Code ran without runtime errors"
            )
            memory.set_current_state(error="")
            
            state['status'] = 'complete'
            print(f"--> [Sandbox Execution Success]:\n{execution_result['stdout']}")
            return state
        else:
            error_log = f"Runtime/Compiler Error:\n{execution_result['stderr']}"
            
            # Log failure to sliding window and overwrite Tier 1 error state
            memory.log_action(
                action_desc="Executed draft code in E2B sandbox",
                result_desc=f"Failed execution turn {state['iteration_count']}"
            )
            memory.set_current_state(error=error_log)
            
            state['errors'].append(error_log)
            state['status'] = 'coding'
            print(f"--> [Sandbox Failure Detected]: Updated 3-step action window.")
            return state

    # 3. LLM Fallback evaluation
    prompt = (
        f"Review this code for the task: {state['task']}\n"
        f"Code:\n{state['draft_code']}\n"
        "If there are errors, list them clearly. If the code is perfect, output 'APPROVED'."
    )
    
    evaluation = route_task("volume-data-model", prompt)
    
    if "APPROVED" in evaluation:
        memory.log_action(
            action_desc="Evaluator LLM code static review",
            result_desc="Approved"
        )
        memory.set_current_state(error="")
        state['status'] = 'complete'
    else:
        memory.log_action(
            action_desc="Evaluator LLM code static review",
            result_desc="Rejected with code issues"
        )
        memory.set_current_state(error=evaluation)
        state['errors'].append(evaluation)
        state['status'] = 'coding'
        
    return state


# 3. Define the DAG Execution Engine
def execute_graph(user_task: str) -> GraphState:
    """The main loop driving the DAG with memory state management."""
    
    # Initialize Memory Manager for this run session
    memory = MemoryManager()
    
    # Initialize state dictionary
    current_state: GraphState = {
        "task": user_task,
        "plan": "",
        "draft_code": "",
        "errors": [],
        "iteration_count": 0,
        "status": "planning",
        "memory": memory
    }
    
    print(f"INITIALIZING DAG FOR TASK: {user_task}")
    
    while current_state["status"] not in ["complete", "failed"]:
        
        # Guardrail Check
        if current_state["iteration_count"] >= MAX_AGENT_TURNS:
            print("\n[CRITICAL] Max iterations reached. Forcing failure state to save compute.")
            current_state["status"] = "failed"
            break
            
        print(f"--> Current State: {current_state['status'].upper()} | Iteration: {current_state['iteration_count']}")
        
        # Directed Routing
        if current_state["status"] == "planning":
            current_state = planner_node(current_state)
            
        elif current_state["status"] == "coding":
            current_state = engineer_node(current_state)
            
        elif current_state["status"] == "evaluating":
            current_state = evaluator_node(current_state)

    print(f"\nFINAL STATUS: {current_state['status'].upper()}")
    return current_state


# Testing the workflow
if __name__ == "__main__":
    task = "Write a Python script that implements a matrix-based Caesar cipher. Ensure the text padding algorithm handles strings that do not perfectly align with the matrix dimensions."
    final_output = execute_graph(task)
    
    if final_output["status"] == "complete":
        print("\nSUCCESS. Final Code Output:\n")
        print(final_output["draft_code"])
    else:
        print("\nFAILED. Review the raw error log:\n")
        print(final_output["errors"])