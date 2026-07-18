"""
CRYOUS - Cognitive Operating System MVP
Main application entry point.
"""

import sys
from core.command_center import CommandCenter
from core.logger import log_info

def main():
    log_info("Booting CRYOUS Engine...")
    
    # Initialize the core facade
    cc = CommandCenter()
    
    log_info("System boot sequence complete. Entering live execution loop.")
    print("\n==================================================")
    print("CRYOUS v1.0 Core Active. Type 'exit' to shutdown.")
    print("==================================================\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.strip().lower() == 'exit':
                log_info("Shutdown command received. Exiting execution loop.")
                break
                
            # Route the phrase through the system architecture
            system_response = cc.execute_command(user_input)
            print(f"\nCRYOUS: {system_response}\n")
            
        except KeyboardInterrupt:
            # Handle Ctrl+C cleanly without ugly terminal tracebacks
            print("\n")
            log_info("System forced to terminate via keyboard interrupt.")
            sys.exit(0)

if __name__ == "__main__":
    main()