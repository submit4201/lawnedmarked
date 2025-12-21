
import os
import sys
# Make sure we can import from backend
sys.path.append(os.getcwd())

from backend.llm.providers.factory import create_provider_from_env

# Helper to verify fix
def verify_fix():
    print(f"Testing AzureAIProjectsProvider Dynamic Model Selection...")
    
    # Mock environment for testing
    os.environ["PROJECTS_ENDPOINT"] = "https://sigal-openai.services.ai.azure.com/api/projects/sigal-openai-project"
    os.environ["PROJECTS_API_KEY"] = "dummy"
    
    target_model = "mistral-small-2503"
    os.environ["PROJECTS_MODEL"] = target_model # Should override default gpt-5-nano
    
    try:
        provider, info = create_provider_from_env("projects")
        print(f"Provider created: {info}")
        
        if provider.config.model == target_model:
            print(f"SUCCESS: Model correctly set to {provider.config.model}")
        else:
            print(f"FAIL: Model is {provider.config.model}, expected {target_model}")
            sys.exit(1)

    except Exception as e:
        print(f"Caught exception during provider init: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_fix()
