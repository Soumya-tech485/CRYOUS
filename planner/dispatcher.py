import os
from dotenv import load_dotenv
from litellm import Router

load_dotenv()

model_list = [
    {
        "model_name": "heavy-reasoning-model", 
        "litellm_params": {
            "model": "openai/gpt-5",
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

routing_fallbacks = [
    {"heavy-reasoning-model": ["volume-data-model", "universal-fallback"]},
    {"fast-sensor-model": ["rapid-inference-fallback", "universal-fallback"]},
    {"volume-data-model": ["background-task-model", "universal-fallback"]},
    {"background-task-model": ["universal-fallback"]}
]

dispatcher = Router(
    model_list=model_list,
    fallbacks=routing_fallbacks,
    num_retries=2 
)

def route_task(task_category, prompt_text):
    try:
        response = dispatcher.completion(
            model=task_category,
            messages=[{"role": "user", "content": prompt_text}]
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"CRITICAL ROUTING ERROR: All fallback layers failed. Error: {str(e)}"