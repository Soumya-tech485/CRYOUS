import re
from typing import Dict, Any
from tools.sandbox import run_python_code, run_c_code 

def evaluator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    memory = state["memory"]
    state['iteration_count'] += 1
    code = state['draft_code']
    deps = state.get('dependencies', [])
    execution_result = None
    
    if re.search(r'```python(.*?)```', code, re.DOTALL):
        clean_code = re.search(r'```python(.*?)```', code, re.DOTALL).group(1).strip()
        execution_result = run_python_code(clean_code, deps=deps)
    elif re.search(r'```c(.*?)```', code, re.DOTALL):
        clean_code = re.search(r'```c(.*?)```', code, re.DOTALL).group(1).strip()
        execution_result = run_c_code(clean_code)
    else:
        state['errors'].append("System Error: No valid code block found. Output code inside ```python or ```c blocks.")
        state['status'] = 'coding'
        return state

    if execution_result:
        if execution_result['success']:
            memory.log_action(action_desc="Executed draft code in E2B sandbox", result_desc="Success")
            memory.set_current_state(error="")
            state['status'] = 'complete'
            print(f"--> [Sandbox Execution Success]:\n{execution_result['stdout']}")
            return state
        else:
            stderr = execution_result['stderr']
            
            # The Dependency Trap
            if "ModuleNotFoundError: No module named" in stderr:
                missing_module = stderr.split("'")[1]
                print(f"--> [Sandbox] Registering missing module: {missing_module}")
                state['dependencies'].append(missing_module)
                state['iteration_count'] -= 1 
                state['status'] = 'evaluating'
                return state

            error_log = f"Runtime/Compiler Error:\n{stderr}"
            memory.log_action(action_desc="Executed draft code in E2B sandbox", result_desc=f"Failed execution turn {state['iteration_count']}")
            memory.set_current_state(error=error_log)
            state['errors'].append(error_log)
            state['status'] = 'coding'
            print(f"--> [Sandbox Failure Detected]: Updated 3-step action window.")
            return state

    return state