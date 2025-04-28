import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import json
import sys

logger = logging.getLogger(__name__)

# Load environment variables 
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))
print(f"Looking for .env at: {os.path.join(PROJECT_ROOT, '.env')}")

# --- AI Functions --- #

def evaluate_post_with_ai(post_text):
    """Analyzes the given post text using Google AI (Gemini)."""
    # Only use GOOGLE_API_KEY as specified
    API_KEY = os.getenv("GOOGLE_API_KEY")
    print(f"GOOGLE_API_KEY value: '{API_KEY}'")
    
    if not API_KEY or API_KEY.strip() == "":
        logger.error("evaluate_post_with_ai: GOOGLE_API_KEY not found or empty.")
        return {"success": False, "error": "GOOGLE_API_KEY not configured properly."}

    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as config_error:
        logger.exception(f"evaluate_post_with_ai: Failed to configure Google AI client: {config_error}")
        return {"success": False, "error": f"Google AI client configuration failed: {config_error}"}
        
    logger.info(f"Evaluating post: '{post_text[:50]}...'")
    if not post_text:
        return {"success": False, "error": "Post text cannot be empty."}
         
    prompt = f"""
Analyze the following text post from a political figure or influencer. Provide the analysis as a JSON object with the following keys:
- "sentiment_classification": Classify the primary sentiment (e.g., Positive, Negative, Neutral, Mixed, Assertive, Critical, Supportive).
- "sentiment_justification": Briefly explain the reasoning for the sentiment classification (1-2 sentences).
- "main_topics": A list of 2-4 main political or social topics discussed or implied.
- "suggested_local_data": A list of 1-3 types of local data points or context that would be relevant for formulating a response or understanding the post's impact (e.g., "Politician Voting Record", "Local News Articles on Topic X", "Related Campaign Finance Data", "Demographics of District Y").

Text Post:
{post_text}

Provide the output strictly in JSON format:
"""
    try:
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        analysis_data = json.loads(response_text.strip())
        logger.info("Successfully evaluated post.")
        return {"success": True, "data": analysis_data}
    
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to decode JSON response from AI evaluation: {json_err}")
        raw_response_text = "<Could not retrieve raw text>"
        try: 
            raw_response_text = response.text
        except Exception: 
            pass
        logger.error(f"Raw AI response: {raw_response_text}")
        return {"success": False, "error": f"AI response was not valid JSON.", "raw_response": raw_response_text}
    
    except Exception as e:
        logger.exception(f"Error during AI evaluation: {e}")
        error_msg = f"AI evaluation failed: {e}"
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            try:
                safety_info = response.prompt_feedback
                logger.error(f"AI Safety Feedback: {safety_info}")
                error_msg += f". Safety feedback: {safety_info}"
            except Exception as safety_e: 
                logger.error(f"Failed to retrieve safety feedback: {safety_e}")
        return {"success": False, "error": error_msg}


def generate_response(prompt):
    """Generates a text response from Google AI based on the provided prompt."""
    # Only use GOOGLE_API_KEY as specified 
    API_KEY = os.getenv("GOOGLE_API_KEY")
    if not API_KEY or API_KEY.strip() == "":
        logger.error("generate_response: GOOGLE_API_KEY not found or empty.")
        return {"success": False, "error": "GOOGLE_API_KEY not configured properly."}

    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as config_error:
        logger.exception(f"generate_response: Failed to configure Google AI client: {config_error}")
        return {"success": False, "error": f"Google AI client configuration failed: {config_error}"}

    logger.info(f"Generating response for prompt starting with: '{prompt[:60]}...'")
    if not prompt:
        return {"success": False, "error": "Prompt cannot be empty."}
         
    try:
        response = model.generate_content(prompt)
        
        if not response.parts:
            block_reason = "Unknown or no parts generated"
            safety_info = None
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                safety_info = response.prompt_feedback
                block_reason = safety_info.block_reason.name if hasattr(safety_info, 'block_reason') else "Blocked, reason unspecified"
            logger.error(f"AI generation blocked or empty. Reason: {block_reason}. Safety feedback: {safety_info}")
            return {"success": False, "error": f"AI generation failed or was blocked ({block_reason})."} 
        
        generated_text = response.text
        logger.info("Successfully generated response.")
        return {"success": True, "data": {"generated_text": generated_text}}
    
    except Exception as e:
        logger.exception(f"Error during AI generation: {e}")
        error_msg = f"AI generation failed: {e}"
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            try:
                safety_info = response.prompt_feedback
                logger.error(f"AI Safety Feedback: {safety_info}")
                error_msg += f". Safety feedback: {safety_info}"
            except Exception as safety_e: 
                logger.error(f"Failed to retrieve safety feedback: {safety_e}")
        return {"success": False, "error": error_msg}


# Example Usage (for testing this script directly)
if __name__ == '__main__':
    # Add project root to path to allow importing logging_config from utils
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_mining_dir = os.path.dirname(current_dir) 
    scripts_dir = os.path.dirname(data_mining_dir)
    project_root = os.path.dirname(scripts_dir)  # Updated to match the corrected PROJECT_ROOT
    sys.path.insert(0, scripts_dir) 

    # Debug: Print environment variables related to API keys
    print("\n--- Environment Variables Debug ---")
    print(f"GOOGLE_API_KEY exists: {os.getenv('GOOGLE_API_KEY') is not None}")
    print(f"GOOGLE_API_KEY value length: {len(os.getenv('GOOGLE_API_KEY', ''))}")
    if os.getenv('GOOGLE_API_KEY'):
        print(f"GOOGLE_API_KEY first 5 chars: '{os.getenv('GOOGLE_API_KEY')[:5]}...'")
    
    # Load .env manually as a test
    print("\n--- Manual .env File Check ---")
    env_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_path):
        print(f".env file exists at {env_path}")
        try:
            with open(env_path, 'r') as f:
                env_content = f.read()
                # Print the line with GOOGLE_API_KEY if it exists (without showing the full key)
                for line in env_content.splitlines():
                    if line.startswith('GOOGLE_API_KEY='):
                        key_value = line.split('=', 1)[1] if '=' in line else ''
                        print(f"Found GOOGLE_API_KEY line in .env, value length: {len(key_value)}")
                        print(f"Value begins with: '{key_value[:5] if len(key_value) >= 5 else key_value}'...")
                        break
                else:
                    print("GOOGLE_API_KEY line not found in .env file")
        except Exception as e:
            print(f"Error reading .env file: {e}")
    else:
        print(f".env file not found at {env_path}")

    try:
        from utils.logging_config import setup_logging
        setup_logging(log_level=logging.DEBUG)
        logger.info("Logging configured via utils.")
    except ImportError as import_err:
        print(f"Could not import logging_config: {import_err}. Using basic logging.")
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__) 

    # Check if the GOOGLE_API_KEY is present and not empty
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and api_key.strip() != "":
        print(f"GOOGLE_API_KEY found with non-empty value")
        print("--- Testing Post Evaluation ---")
        test_post = "Just voted YES on the border security bill. We need strong borders to keep America safe! #MAGA #BuildTheWall"
        eval_result = evaluate_post_with_ai(test_post)
        print(json.dumps(eval_result, indent=2))

        print("\n--- Testing Response Generation ---")
        test_prompt = "Draft a short, supportive tweet reply to the following post, emphasizing agreement on border security: 'Just voted YES on the border security bill. We need strong borders to keep America safe! #MAGA #BuildTheWall'"
        gen_result = generate_response(test_prompt)
        print(json.dumps(gen_result, indent=2))
    else:
        print(f"GOOGLE_API_KEY is {'not set' if api_key is None else 'empty'}")
        print("Cannot run tests: GOOGLE_API_KEY not found or empty in .env file")

    print("\n--- Post Evaluator Script Finished ---") 