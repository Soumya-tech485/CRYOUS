# tools/file_ops.py
import os

def read_local_file(file_path: str) -> str:
    """
    Reads the content of a local file and returns it.
    Use this tool when the user asks about the contents of a specific file or codebase.
    """
    # 1. Security Check: Prevent the AI from reading sensitive system files outside the project
    if ".." in file_path or file_path.startswith("/"):
        return "ERROR: Access denied. Cannot navigate outside the project directory."

    if ".env" in file_path:
        return "ERROR: Access denied. System configuration files are classified."
     
    # 2. File verification
    if not os.path.exists(file_path):
        return f"ERROR: The file '{file_path}' does not exist in the current directory."
        
    # 3. Read and return the content
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return f"--- START OF {file_path} ---\n{content}\n--- END OF {file_path} ---"
    except Exception as e:
        return f"ERROR: Failed to read file. Exception: {str(e)}"