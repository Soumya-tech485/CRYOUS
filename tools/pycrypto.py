import numpy as np
from sympy import Matrix

class MatrixCipher:
    def __init__(self):
        # A carefully selected 2x2 Key Matrix. 
        # Det(K) = (3*5) - (3*2) = 9. 
        # 9 is coprime to 256, guaranteeing reversibility.
        self.key = np.array([[3, 3], 
                             [2, 5]])
        
        # Compute the modular inverse matrix at initialization
        self.inv_key = np.array(Matrix(self.key).inv_mod(256)).astype(int)

    def encrypt_text(self, text: str) -> str:
        # Convert text to byte values
        byte_vals = [ord(c) for c in text]
        
        # Pad with a space (ASCII 32) if length is odd for a 2x2 matrix
        if len(byte_vals) % 2 != 0:
            byte_vals.append(32)
            
        vector_blocks = np.array(byte_vals).reshape(-1, 2)
        encrypted_blocks = np.dot(vector_blocks, self.key) % 256
        
        # Convert back to string representation
        return ''.join([chr(val) for val in encrypted_blocks.flatten()])

    def decrypt_text(self, cipher_text: str) -> str:
        byte_vals = [ord(c) for c in cipher_text]
        vector_blocks = np.array(byte_vals).reshape(-1, 2)
        
        # Multiply by modular inverse to reverse
        decrypted_blocks = np.dot(vector_blocks, self.inv_key) % 256
        
        return ''.join([chr(val) for val in decrypted_blocks.flatten()]).rstrip()

# --- Local Verification Test ---
if __name__ == "__main__":
    cipher = MatrixCipher()
    original_data = "CRYOUS_OS_INIT"
    
    encrypted = cipher.encrypt_text(original_data)
    decrypted = cipher.decrypt_text(encrypted)
    
    print(f"Original:  {original_data}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    
    assert original_data == decrypted, "CRITICAL FAILURE: Asymmetric matrix inversion."