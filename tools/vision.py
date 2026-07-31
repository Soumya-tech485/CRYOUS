import os
import base64
from tools.matrix_cipher import MatrixCipher

# Initialize the cryptographic engine globally
cipher_engine = MatrixCipher()

# Ensure the sandbox directory exists when the system starts
SANDBOX_DIR = "sandbox_temp"
if not os.path.exists(SANDBOX_DIR):
    os.makedirs(SANDBOX_DIR)

def read_file(file_path: str) -> str:
    """Reads content of a local file. Attempts to decrypt first, falls back to plain text."""
    if ".." in file_path or file_path.startswith("/"):
        return "ERROR: Access denied. Directory traversal detected."
    if ".env" in file_path:
        return "ERROR: Access denied. Classified."
    if not os.path.exists(file_path):
        return f"ERROR: '{file_path}' does not exist."
        
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Attempt to decode and decrypt (assuming files written by CRYOUS are encrypted)
        try:
            encrypted_bytes = base64.b64decode(content)
            encrypted_content = encrypted_bytes.decode('utf-8')
            decrypted_content = cipher_engine.decrypt_text(encrypted_content)
            return f"--- START OF {file_path} (DECRYPTED) ---\n{decrypted_content}\n--- END OF {file_path} ---"
        except Exception:
            # Fallback: File is likely just plain text (e.g., requirements.txt, Python scripts)
            return f"--- START OF {file_path} (PLAIN TEXT) ---\n{content}\n--- END OF {file_path} ---"
            
    except Exception as e:
        return f"ERROR: Failed to read file. Exception: {str(e)}"

def write_local_file(file_path: str, content: str) -> str:
    """Stages, validates, and deploys encrypted files."""
    if ".." in file_path or file_path.startswith("/"):
        return "ERROR: Access denied."
    if ".env" in file_path:
        return "ERROR: Access denied. Classified."
        
    # Phase 1: STAGE (Write to the sandbox, not the real computer)
    temp_file_path = os.path.join(SANDBOX_DIR, "temp_" + os.path.basename(file_path))
    
    try:
        encrypted_payload = cipher_engine.encrypt_text(content)
        encrypted_bytes = encrypted_payload.encode('utf-8')
        safe_content = base64.b64encode(encrypted_bytes).decode('utf-8')
        
        with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
            temp_file.write(safe_content)
    except Exception as e:
        return f"ERROR: Staging failed. {str(e)}"

    # Phase 2: VALIDATE (Test the sandboxed file)
    try:
        # We try to read and decrypt the temporary file we just made.
        # If the math breaks or formatting is wrong, this will trigger an error.
        with open(temp_file_path, 'r', encoding='utf-8') as temp_file:
            test_content = temp_file.read()
            
        test_bytes = base64.b64decode(test_content).decode('utf-8')
        _ = cipher_engine.decrypt_text(test_bytes) 
    except Exception as e:
        # Phase 4 (Fail): CLEAN (Delete the bad file to free memory)
        os.remove(temp_file_path)
        return f"ERROR: Validation failed. File corrupted during staging. {str(e)}"

    # Phase 3 & 4 (Success): DEPLOY and CLEAN
    try:
        # os.replace automatically moves the file to the real location.
        # If an old file exists there, it overwrites it safely. 
        # Moving it automatically removes it from the sandbox, cleaning the space.
        os.replace(temp_file_path, file_path)
        return f"SUCCESS: File validated and deployed safely to {file_path}"
    except Exception as e:
        return f"ERROR: Deployment failed. {str(e)}"