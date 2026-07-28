import os
from dotenv import load_dotenv
from typing import Dict, Any
from e2b_code_interpreter import Sandbox

# Load environment variables
load_dotenv()

def run_python_code(code_str: str, timeout_sec: int = 60) -> Dict[str, Any]:
    """
    Executes Python code securely in an isolated E2B cloud sandbox.
    """
    cleaned_code = code_str.replace("```python", "").replace("```", "").strip()
    
    try:
        # Explicitly pass the API key to the Sandbox creation
        api_key = os.getenv("E2B_API_KEY")
        with Sandbox.create(api_key=api_key) as sandbox: 
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
    """
    Compiles and executes C code securely in the E2B sandbox.
    """
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

if __name__ == "__main__":
    # Debug: Check if Python actually sees the key
    current_key = os.getenv("E2B_API_KEY")
    if current_key:
        print(f"DEBUG: API Key found! It starts with: {current_key[:8]}...")
    else:
        print("DEBUG: API Key is STILL missing. The .env file is not being read correctly.")

    # Test execution
    test_code = "print('E2B Sandbox environment active. Output test success.')"
    res = run_python_code(test_code)
    print("Sandbox Test Result:", res)