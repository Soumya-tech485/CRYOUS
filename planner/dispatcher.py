import os
from dotenv import load_dotenv
from litellm import Router

# Load the environment variables from the .env file in the root directory
load_dotenv()

# 1. Define the pool of 6 free models using standard LiteLLM formatting
model_list = [
    {
        "model_name": "heavy-reasoning-model", 
        "litellm_params": {
            "model": "openai/gpt-5", # Calls GPT-5 via the OpenAI compatible endpoint
            "api_base": "https://models.github.ai/inference",
            "api_key": os.environ.get("GITHUB_PAT"),
        }
    },
    {
        "model_name": "fast-sensor-model", 
        "litellm_params": {
            "model": "groq/llama3-8b-8192",
            "api_key": os.environ.get("GROQ_API_KEY"),
        }
    },
    {
        "model_name": "volume-data-model", 
        "litellm_params": {
            "model": "gemini/gemini-3.5-flash-lite", 
            "api_key": os.environ.get("GEMINI_API_KEY"),
        }
    },
    {
        "model_name": "background-task-model", 
        "litellm_params": {
            "model": "mistral/mistral-large-latest", 
            "api_key": os.environ.get("MISTRAL_API_KEY"),
        }
    },
    {
        "model_name": "rapid-inference-fallback", 
        "litellm_params": {
            "model": "cerebras/llama3.1-8b",
            "api_key": os.environ.get("CEREBRAS_API_KEY"),
        }
    },
    {
        "model_name": "universal-fallback", 
        "litellm_params": {
            "model": "openrouter/auto", 
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
        }
    }
]

# 2. Configure the 6-layer Fallback Chain
# If a model hits a rate limit, LiteLLM automatically drops down to the next provider
routing_fallbacks = [
    {"heavy-reasoning-model": ["volume-data-model", "universal-fallback"]},
    {"fast-sensor-model": ["rapid-inference-fallback", "universal-fallback"]},
    {"volume-data-model": ["background-task-model", "universal-fallback"]},
    {"background-task-model": ["universal-fallback"]}
]

# 3. Initialize the Router
dispatcher = Router(
    model_list=model_list,
    fallbacks=routing_fallbacks,
    num_retries=2 # Retries a failed provider twice before triggering the fallback
)

# 4. Main routing function for daemon.py to call
def route_task(task_category, prompt_text):
    """
    Executes the prompt using the most optimal model based on the task category.
    Valid categories: 'heavy-reasoning-model', 'fast-sensor-model', 
                      'volume-data-model', 'background-task-model'
    """
    try:
        response = dispatcher.completion(
            model=task_category,
            messages=[{"role": "user", "content": prompt_text}]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"CRITICAL ROUTING ERROR: All fallback layers failed. Error: {str(e)}"

# Quick execution block to verify the GPT-5 endpoint is working
if __name__ == "__main__":
    print("Testing GPT-5 via GitHub Models...")
    test_heavy = route_task(
        "heavy-reasoning-model", 
        "Debug the matrix inversion logic for this cryptography script."
    )
    print("Result:\n", test_heavy)