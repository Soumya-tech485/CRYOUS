from brain.llm import LLMProvider
import os

def main():
    print("Booting CRYOUS Cognitive Operating System...")
    
    # 1. Allocate memory and run __init__ (The Setup)
    engine = LLMProvider()
    
    print("System Online. Type 'exit' or 'quit' to terminate.")
    print("-" * 50)

    # 2. The Infinite Execution Loop
    while True:
        try:
            # Grab user input
            user_input = input("\nUSER > ")

            
            
            # Prevent sending empty strings to the API
            if not user_input.strip():
                continue

            # 1. Deterministic System Commands (The Interceptor)
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command in ['/exit', '/quit']:
                    print("\nInitiating shutdown sequence. Goodbye.")
                    break
                
                elif command == '/clear':
                    # Clears the terminal 
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue 
                
                else:
                    print(f"[SYSTEM] Unrecognized command: '{command}'")
                    continue

            # 4. Dereference the pointer and call the method (The Action)
            response = engine.generate_chat_response(user_input)
            
            print(f"CRYOUS > {response}")

        except KeyboardInterrupt:
            # Handles the user pressing Ctrl+C safely
            print("\n\nForce quit detected. Shutting down...")
            break
        except Exception as e:
            print(f"\n[SYSTEM ERROR]: {e}")

if __name__ == "__main__":
    main()