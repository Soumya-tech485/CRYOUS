import sys
import signal
import logging
from graph_state import execute_graph

# Configure logging for the daemon
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def graceful_shutdown(signum, frame):
    """Trap termination signals to exit cleanly."""
    print("\n\n[DAEMON] Shutting down CRYOUS orchestration daemon gracefully. Goodbye!")
    sys.exit(0)

def main():
    """Main REPL loop for the agent orchestration daemon."""
    # Register signal handlers for graceful exit
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    print("===================================================")
    print(" CRYOUS AGENT ORCHESTRATOR DAEMON - INITIALIZED    ")
    print("===================================================")
    print("Type 'exit' or 'quit' to shut down.")
    print("Press Ctrl+C at any time to force quit.\n")
    
    while True:
        try:
            # 1. Ingest Task
            user_task = input("\n[CRYOUS] Enter task objective > ").strip()
            
            if not user_task:
                continue
            if user_task.lower() in ['exit', 'quit']:
                print("[DAEMON] Received exit command.")
                break
                
            logging.info(f"Dispatching task to DAG: {user_task}")
            
            # 2. Execute Graph (Starts the Node Routing)
            # This links directly to your GraphState logic
            final_state = execute_graph(user_task)
            
            # 3. Handle End State
            if final_state["status"] == "complete":
                logging.info("Task achieved successfully.")
                print("\n[DAEMON] Task Complete. Final Output:")
                print("---------------------------------------------------")
                print(final_state["draft_code"])
                print("---------------------------------------------------")
            else:
                logging.warning("Task failed or reached maximum iteration limit.")
                print("\n[DAEMON] Task Failed. Review the final error trace:")
                print("---------------------------------------------------")
                for err in final_state.get("errors", []):
                    print(err)
                print("---------------------------------------------------")
                
        except EOFError:
            print("\n[DAEMON] EOF received. Shutting down.")
            break
        except KeyboardInterrupt:
            # Handled by the signal interceptor, but caught here for fallback
            break
        except Exception as e:
            logging.error(f"Daemon encountered an unexpected exception: {e}")
            print(f"\n[DAEMON CRASH PROTECTION] Caught exception: {e}")

if __name__ == "__main__":
    main()