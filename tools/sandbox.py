import os
from dotenv import load_dotenv
from typing import Dict, Any, List
from e2b_code_interpreter import Sandbox

load_dotenv()

def run_python_code(code_str: str, deps: List[str] = None, timeout_sec: int = 60) -> Dict[str, Any]:
    """Executes Python code securely in an isolated E2B cloud sandbox and handles dynamic dependencies."""
    cleaned_code = code_str.replace("```python", "").replace("```", "").strip()
    
    try:
        api_key = os.getenv("E2B_API_KEY")
        with Sandbox.create(api_key=api_key) as sandbox:
            
            # Auto-install tracked dependencies into the new ephemeral sandbox
            if deps:
                for dep in set(deps):
                    print(f"--> [Sandbox] Injecting dependency: pip install {dep}")
                    sandbox.commands.run(f"pip install {dep}", timeout=120)
            
            execution = sandbox.run_code(cleaned_code, timeout=timeout_sec) 
            
            if execution.error: 
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"{execution.error.name}: {execution.error.value}",
                    "exit_code": 1
                }
            
            stdout_output = ""
            if execution.results:
                for result in execution.results:
                    stdout_output += result.text + "\n"
            if execution.logs.stdout:
                stdout_output += "\n".join(execution.logs.stdout)
                
            stderr_output = "\n".join(execution.logs.stderr) if execution.logs.stderr else ""
            
            return {
                "success": True,
                "stdout": stdout_output.strip(),
                "stderr": stderr_output.strip(),
                "exit_code": 0
            }
            
    except Exception as e:
         return {
            "success": False,
            "stdout": "",
            "stderr": f"SYSTEM/E2B ERROR: {str(e)}",
            "exit_code": -1
        }

def run_c_code(code_str: str, timeout_sec: int = 60) -> Dict[str, Any]:
    """Compiles and executes C code securely in the E2B sandbox."""
    cleaned_code = code_str.replace("```c", "").replace("```", "").strip()
    
    try:
        api_key = os.getenv("E2B_API_KEY")
        with Sandbox.create(api_key=api_key) as sandbox:
            sandbox.files.write("/home/user/main.c", cleaned_code)
            
            compile_res = sandbox.commands.run(
                "gcc /home/user/main.c -o /home/user/main", 
                timeout=timeout_sec
            )
            
            if compile_res.exit_code != 0:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": compile_res.stderr,
                    "exit_code": compile_res.exit_code
                }
                
            run_res = sandbox.commands.run("/home/user/main", timeout=timeout_sec)
            
            return {
                "success": run_res.exit_code == 0,
                "stdout": run_res.stdout,
                "stderr": run_res.stderr,
                "exit_code": run_res.exit_code
            }
            
    except Exception as e:
         return {
            "success": False,
            "stdout": "",
            "stderr": f"SYSTEM/E2B ERROR: {str(e)}",
            "exit_code": -1
        }