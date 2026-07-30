import re
from typing import TypedDict, List
from planner.dispatcher import route_task
from memory.core_memory import MemoryManager
from core.engineer import engineer_node
from core.evaluator import evaluator_node

class GraphState(TypedDict):
    task: str
    plan: str
    draft_code: str
    errors: List[str]
    dependencies: List[str]
    iteration_count: int
    status: str
    memory: MemoryManager 

MAX_AGENT_TURNS = 3

def planner_node(state: GraphState) -> GraphState:
    memory = state["memory"]
    memory.set_current_state(objective=state['task'])
    
    prompt = f"Create a step-by-step engineering plan to solve this task: {state['task']}"
    plan_output = route_task("heavy-reasoning-model", prompt)
    
    memory.log_action("Planner generated execution plan", "Plan generated successfully")
    state['plan'] = plan_output
    state['status'] = 'coding'
    return state

def execute_graph(user_task: str) -> GraphState:
    memory = MemoryManager()
    
    current_state: GraphState = {
        "task": user_task,
        "plan": "",
        "draft_code": "",
        "errors": [],
        "dependencies": [],
        "iteration_count": 0,
        "status": "planning",
        "memory": memory
    }
    
    print(f"INITIALIZING DAG FOR TASK: {user_task}")
    
    while current_state["status"] not in ["complete", "failed"]:
        
        if current_state["iteration_count"] >= MAX_AGENT_TURNS:
            last_error = current_state['errors'][-1] if current_state['errors'] else ""
            if current_state["iteration_count"] == MAX_AGENT_TURNS and any(e in last_error for e in ["SyntaxError", "IndentationError", "NameError"]):
                print("\n[INFO] Minor syntax error detected on final turn. Granting 1 grace turn.")
            else:
                print("\n[CRITICAL] Max iterations reached. Forcing failure state to save compute.")
                current_state["status"] = "failed"
                break
            
        print(f"--> Current State: {current_state['status'].upper()} | Iteration: {current_state['iteration_count']}")
        
        if current_state["status"] == "planning":
            current_state = planner_node(current_state)
        elif current_state["status"] == "coding":
            current_state = engineer_node(current_state)
        elif current_state["status"] == "evaluating":
            current_state = evaluator_node(current_state)

    print(f"\nFINAL STATUS: {current_state['status'].upper()}")
    return current_state