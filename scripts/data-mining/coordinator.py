# Data Mining Coordinator
# This script will dispatch mining tasks based on requests. 

import sys
import os
import json
import threading
import time # For simulating work and timestamps
import logging # Import logging
from datetime import datetime

# Import the setup function
try:
    from .utils.logging_config import setup_logging
except ImportError:
    # Fallback if utils structure isn't there or path issues
    def setup_logging(log_level=logging.INFO, log_file=None):
        logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s', force=True)
        print("Fallback basic logging configured.", file=sys.stderr)

# Configure logging (e.g., INFO level, adjust as needed, maybe based on env var?)
# Could also add a file handler here: setup_logging(log_file='path/to/coordinator.log')
setup_logging(log_level=logging.DEBUG) # Use DEBUG for more detail during dev

# Get a logger for this module
logger = logging.getLogger(__name__) # Use module name

# Add parent directories to path to allow imports
# Assuming api_bridge.py calls this script directly
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
project_dir = os.path.dirname(scripts_dir)
# Ensure the path to the db module is included
sys.path.insert(0, scripts_dir) # Add scripts dir first for db module
sys.path.append(project_dir) # To potentially import db utils later

# --- Import Real Database Manager --- #
try:
    from db.database_manager import DatabaseManager
    database_manager = DatabaseManager() # Instantiate the real manager
    logger.info("Successfully imported and instantiated real DatabaseManager.")
except ImportError as e:
    logger.exception("Failed to import DatabaseManager from db.database_manager. Falling back to DummyDB.")
    # Define Dummy DB only if the real one fails to import
    class DummyDB:
         def search_entities(self, query): # Keep search as fallback if needed?
             print(f"DUMMY DB SEARCH: Query '{query}'", file=sys.stderr)
             time.sleep(0.5)
             return [
                 {"id": "pol_dummy_1", "type": "politician", "name": f"Politician matching '{query}'", "category": "Politician", "bio": "Dummy bio for politician."},
                 {"id": "inf_dummy_1", "type": "influencer", "name": f"Influencer matching '{query}'", "category": "Social Media", "bio": "Dummy bio for influencer."}
             ]
    database_manager = DummyDB()
# --- END Database Manager Import --- #

# --- Keep Dummy Sources/Processors for now if other handlers need them --- #
try:
    from .sources import youtube_channel, twitter_profile, fec_lookup, voting_records, committees, influencer_metrics, influencer_stances
    from .processors import post_evaluator
except ImportError as e:
    logger.warning(f"Error importing source/processor modules: {e}. Some functionality might use dummies.", exc_info=True)
    # Define dummy functions if import fails, for basic testing
    class DummySource:
        def fetch_latest_data(*args, **kwargs):
            # ... (dummy implementation) ...
            return {"success": True, "data": {"id": "dummy_tweet_123", "text": "This is dummy tweet content", "timestamp": time.time()}}
        def fetch_latest_tweet(*args, **kwargs): 
             return DummySource.fetch_latest_data(*args, **kwargs)
    youtube_channel = twitter_profile = fec_lookup = DummySource()
    # ... (other dummy sources/processors as needed by other handlers) ...
    class DummyEvaluator:
        def evaluate_post_with_ai(post_text):
            # ... (dummy implementation) ...
             print(f"DUMMY EVAL: Analyzing '{post_text[:30]}...'") # Add print back for visibility
             time.sleep(0.1)
             return {"success": True, "data": {"sentiment_classification": "Neutral", "sentiment_justification": "Dummy analysis.", "main_topics": ["Dummy Topic"], "suggested_local_data": ["Politician Voting Record"]}}
        def generate_response(prompt):
             logger.warning("DUMMY generate_response called. Needs implementation in real AI module.")
             return {"success": True, "data": {"generated_text": f"[DUMMY RESPONSE to prompt starting with: {prompt[:50]}...]"}}
    post_evaluator = DummyEvaluator()
    # ... (rest of dummy source definitions) ...
    class DummyCommitteesSource: # Keep for handle_fetch_request if needed
        def fetch_committees(*args, **kwargs): # Add dummy implementation back
            print(f"DUMMY COMMITTEES FETCH: {args} {kwargs}", file=sys.stderr)
            time.sleep(0.2)
            return {"success": True, "data": [{"id": "COM_DUM", "name": "Dummy Committee", "rank": 1, "title": "Chair"}]}
    committees = DummyCommitteesSource()
    class DummyMetricsSource: # Keep for handle_fetch_request if needed
         def fetch_metrics(*args, **kwargs): # Add dummy implementation back
            print(f"DUMMY METRICS FETCH: {args} {kwargs}", file=sys.stderr)
            time.sleep(0.2)
            return {"success": True, "data": {"follower_count": 12345, "engagement_rate": 1.23}}
    influencer_metrics = DummyMetricsSource()
    class DummyStancesSource: # Keep for handle_fetch_request if needed
        def fetch_stances(*args, **kwargs): # Add dummy implementation back
            print(f"DUMMY STANCES FETCH: {args} {kwargs}", file=sys.stderr)
            time.sleep(0.2)
            return {"success": True, "data": [{"topic": "Dummy Topic", "position": "For", "summary": "Dummy stance."}]}
    influencer_stances = DummyStancesSource()
    # Ensure voting_records is defined, even if it's just None, if import failed
    if 'voting_records' not in locals():
        voting_records = None 
        logger.error("Failed to import real voting_records source AND no dummy fallback defined!")
# --- END Dummy Source/Processor Setup --- #


# --- Background Task Processing (Keep structure, but don't call queue_background_task for evaluation flow) ---
background_tasks = []
task_lock = threading.Lock()
processing_thread = None
stop_processing = threading.Event()

def queue_background_task(task_details):
    """Adds a task to the background queue."""
    with task_lock:
        background_tasks.append(task_details)
        logger.info(f"Queued background task: {task_details}") # Use logger

def process_background_tasks():
    """Continuously processes tasks from the queue."""
    logger.info("Background task processor started.") # Use logger
    while not stop_processing.is_set():
        task = None
        with task_lock:
            if background_tasks:
                task = background_tasks.pop(0)

        if task:
            logger.info(f"Processing background task: {task}") # Use logger
            try:
                # --- Schema Check Placeholder ---
                logger.debug(f"(Placeholder) Schema check for field '{task.get('field', 'N/A')}'")

                # --- Broader Data Mining ---
                entity_type = task.get('entity_type')
                field = task.get('field')
                reference_id = task.get('reference_id') # The ID that triggered the fetch

                if entity_type and field and reference_id:
                    relevant_ids = database_manager.get_relevant_entities(entity_type, reference_id)
                    fetch_function = get_fetch_function(entity_type, field)

                    if fetch_function and relevant_ids:
                        logger.info(f"Starting broader mining for '{field}' on {len(relevant_ids)} entities.") # Use logger
                        for entity_id in relevant_ids:
                            try:
                                logger.debug(f"Background fetching '{field}' for {entity_type} {entity_id}") # Use logger
                                fetched_data_result = fetch_function(entity_id=entity_id) # Adjust params/handle context
                                if fetched_data_result.get('success'):
                                    database_manager.update_entity_field(entity_type, entity_id, field, fetched_data_result['data'])
                                else:
                                    # Use logger warning
                                    logger.warning(f"Background fetch failed for {entity_id}: {fetched_data_result.get('error', 'Unknown')}")
                                time.sleep(0.2)
                            except Exception as e:
                                # Use logger exception
                                logger.exception(f"Error background fetching for {entity_id}")
                    else:
                        # Use logger warning
                        logger.warning(f"Could not determine fetch function or relevant entities for task: {task}")

            except Exception as e:
                # Use logger exception
                logger.exception(f"Error processing background task {task}")
        else:
            time.sleep(1)
    logger.info("Background task processor stopped.") # Use logger

def start_background_processor():
    """Starts the background task processing thread if not already running."""
    global processing_thread
    if processing_thread is None or not processing_thread.is_alive():
        stop_processing.clear()
        processing_thread = threading.Thread(target=process_background_tasks, daemon=True)
        processing_thread.start()
        logger.info("Background processor thread started.") # Use logger

def stop_background_processor():
    """Stops the background task processing thread."""
    global processing_thread
    if processing_thread and processing_thread.is_alive():
        stop_processing.set()
        processing_thread.join(timeout=5)
        logger.info("Background processor thread stopped.") # Use logger
        processing_thread = None

# --- Request Handling ---

def get_fetch_function(entity_type, field):
    """Maps entity type and field to the correct data source function.
       Returns the function itself.
    """
    if entity_type == 'influencer':
        if field == 'latest_videos':
             return youtube_channel.fetch_latest_data
        elif field == 'metrics': # Add mapping for metrics
            return influencer_metrics.fetch_metrics
        elif field == 'stances': # Add mapping for stances
            return influencer_stances.fetch_stances
        # Add other influencer fields here
    elif entity_type == 'politician':
        if field == 'latest_tweet':
            return twitter_profile.fetch_latest_tweet
        elif field == 'fec_filings':
             return fec_lookup.fetch_latest_data
        elif field == 'voting_record': 
            if voting_records and hasattr(voting_records, 'fetch_recent_votes'):
                return voting_records.fetch_recent_votes
            else:
                logger.error("voting_records module not available for fetch_recent_votes.")
                return None # Indicate function not available
        elif field == 'committees': # Add mapping for committees
            return committees.fetch_committees
        # Add other politician fields here
    return None

def handle_fetch_request(request_details):
    """Handles simple data fetch requests (check local, fetch external, queue background)."""
    entity_type = request_details.get('entity_type')
    entity_id = request_details.get('entity_id')
    field = request_details.get('field')
    context = request_details.get('context', {})
    logger.info(f"Handling FETCH request for {entity_type}/{entity_id}/{field}") # Use logger

    # Fields that rely *only* on background updates (no live fetch on demand)
    background_updated_fields = ['voting_record', 'committees'] # Add other similar fields here

    # 1. Check Local Data
    local_data = database_manager.get_entity_field(entity_type, entity_id, field)
    is_stale = False # Add staleness check logic here if needed even for background fields
    data_missing = local_data is None

    if not data_missing and not is_stale:
        logger.info(f"Found local data for {field}. Returning.") # Use logger
        return {"success": True, "data": local_data, "source": "local"}

    # 2. If data is missing/stale, decide whether to fetch live or just return
    if field in background_updated_fields:
        logger.info(f"Data missing/stale for background-updated field '{field}'. Returning empty.") # Use logger
        print(f"Coordinator: Data missing/stale for background-updated field '{field}'. Returning empty/error.", file=sys.stderr)
        # Return success=True but with empty data, or success=False? Let's return success=True with empty data.
        # Frontend's populateList will show the 'empty message' in this case.
        return {"success": True, "data": [], "source": "local_empty"}

    # 3. Attempt Live External Fetch (for fields *not* in background_updated_fields)
    print(f"Coordinator: Data missing/stale for '{field}'. Attempting external fetch...", file=sys.stderr)
    fetch_function = get_fetch_function(entity_type, field)

    if not fetch_function:
         # Handle case where it's not a background field but also has no fetch function
         print(f"Coordinator: No fetch function defined for non-background field {entity_type}/{field}", file=sys.stderr)
         return {"success": False, "error": f"Data not found locally and no fetch function defined for {entity_type}/{field}"}

    try:
        # Determine necessary args for the specific fetch function
        if field == 'latest_tweet':
            handle = context.get('twitter_handle') or database_manager.get_entity_field(entity_type, entity_id, 'twitter_handle')
            if not handle:
                return {"success": False, "error": f"Missing twitter_handle for {entity_id}"}
            fetch_result = fetch_function(twitter_handle=handle.lstrip('@'))
        else:
            # Assume other functions might just need entity_id or other context
            fetch_result = fetch_function(entity_id=entity_id, **context)

        if not fetch_result.get('success'):
            # Propagate error from fetch function
            return fetch_result

        fetched_data = fetch_result['data']
        print(f"Coordinator: Returning fetched data for {field} to user.", file=sys.stderr)
        database_manager.update_entity_field(entity_type, entity_id, field, fetched_data)

        # --- Queue Background Task for Enrichment --- #
        # Should we still queue enrichment if data was fetched live?
        # Maybe only queue if the fetch was triggered by something other than direct user request?
        # For now, keep it simple: queue enrichment after successful live fetch.
        queue_background_task({
            "type": "enrich",
            "entity_type": entity_type,
            "field": field,
            "reference_id": entity_id
        })

        return {"success": True, "data": fetched_data, "source": "external"}

    except Exception as e:
        print(f"Coordinator: Error during external fetch/processing for {field}: {e}", file=sys.stderr)
        return {"success": False, "error": f"External fetch/processing failed: {e}"}

def handle_evaluate_request(request_details):
    """Handles requests to evaluate a post (fetch latest, analyze, return). NO background enrichment."""
    entity_type = request_details.get('entity_type')
    entity_id = request_details.get('entity_id')
    context = request_details.get('context', {})

    if entity_type != 'politician': # Currently only support politician post eval
        return {"success": False, "error": "Evaluation only supported for entity_type 'politician'"}

    print(f"Coordinator: Handling EVALUATE request for {entity_type}/{entity_id}", file=sys.stderr)

    # 1. Fetch the latest tweet
    twitter_handle = context.get('twitter_handle') or database_manager.get_entity_field(entity_type, entity_id, 'twitter_handle')
    if not twitter_handle:
        return {"success": False, "error": f"Missing twitter_handle for {entity_id} to fetch tweet"}

    print(f"Coordinator: Fetching latest tweet for {twitter_handle.lstrip('@')}...", file=sys.stderr)
    tweet_fetch_result = twitter_profile.fetch_latest_tweet(twitter_handle=twitter_handle.lstrip('@'))

    if not tweet_fetch_result.get('success'):
        print(f"Coordinator: Failed to fetch tweet for evaluation.", file=sys.stderr)
        return tweet_fetch_result # Return the error from fetch function

    tweet_data = tweet_fetch_result['data']
    tweet_text = tweet_data.get('text')

    if not tweet_text:
         return {"success": False, "error": "Fetched tweet data did not contain text."}

    # 2. Evaluate the tweet text with AI
    print(f"Coordinator: Evaluating tweet text with AI...", file=sys.stderr)
    ai_eval_result = post_evaluator.evaluate_post_with_ai(tweet_text)

    if not ai_eval_result.get('success'):
        print(f"Coordinator: AI evaluation failed.", file=sys.stderr)
        # Return AI error, but include the fetched tweet data for context
        return {
            "success": False,
            "error": ai_eval_result.get('error', 'AI evaluation failed'),
            "fetched_tweet": tweet_data # Include the tweet even if AI fails
        }

    # 3. Combine results and return
    # We choose NOT to queue a background task here deliberately
    combined_data = {
        "tweet": tweet_data,
        "ai_evaluation": ai_eval_result['data']
    }

    print(f"Coordinator: Successfully evaluated tweet.", file=sys.stderr)
    return {"success": True, "data": combined_data}

# NEW: Handler for forced data fetching
def handle_force_fetch_request(request_details):
    """Handles requests to force fetch external data, bypassing local cache/staleness checks."""
    entity_type = request_details.get('entity_type')
    entity_id = request_details.get('entity_id')
    field = request_details.get('field')
    context = request_details.get('context', {}) # Pass context just in case

    print(f"Coordinator: Handling FORCE_FETCH request for {entity_type}/{entity_id}/{field}", file=sys.stderr)

    fetch_function = get_fetch_function(entity_type, field)

    if not fetch_function:
        print(f"Coordinator: No fetch function defined for force fetch: {entity_type}/{field}", file=sys.stderr)
        return {"success": False, "error": f"No fetch function defined for {entity_type}/{field}"}

    try:
        print(f"Coordinator: Executing external fetch for {field}...", file=sys.stderr)
        # Special handling for force_fetch on voting records - trigger the tool update
        if field == 'voting_record':
             logger.info("Force fetch requested for voting_record. Running congress tool with --force.")
             if not voting_records.run_congress_tool(force_update=True):
                 return {"success": False, "error": "Failed to run congress data tool to force update votes."}
             # After forcing update, call the standard fetch function to get latest parsed data
             fetch_result = fetch_function(entity_id=entity_id, **context) 
        # --- Original force fetch logic for other fields --- #
        # elif field == 'latest_tweet': # Should this even be force-fetchable? Probably not via this mechanism.
        #      # Force fetch likely doesn't apply to latest_tweet which is always live fetched by evaluate
        #      return {"success": False, "error": "Force fetch not applicable to latest_tweet"}
        else:
            # Assume other functions might just need entity_id or other context
            fetch_result = fetch_function(entity_id=entity_id, **context)
        # --- End original logic --- #

        if not fetch_result.get('success'):
            # Propagate error from fetch function
            print(f"Coordinator: Force fetch failed for {field}: {fetch_result.get('error')}", file=sys.stderr)
            return fetch_result

        fetched_data = fetch_result['data']
        print(f"Coordinator: Force fetch successful for {field}. Updating database...", file=sys.stderr)
        
        # Update the database with the newly fetched data
        # Use the real manager now
        update_success = database_manager.update_entity_field(entity_type, entity_id, field, fetched_data)
        if not update_success:
             logger.warning(f"Database update failed after force fetch for {entity_type}/{entity_id}/{field}")
             # Decide whether to return error or just log it - let's log and still return data
        
        # Return the fresh data to the frontend
        return {"success": True, "data": fetched_data, "source": "external_forced"}

    except Exception as e:
        print(f"Coordinator: Error during forced external fetch for {field}: {e}", file=sys.stderr)
        return {"success": False, "error": f"Forced external fetch failed: {e}"}

# NEW: Handler for generating intelligence content
def handle_generate_intel_request(request_details):
    """Handles intelligence generation requests."""
    format = request_details.get('format') # email, post, reply, etc.
    context = request_details.get('context')

    print(f"Coordinator: Handling GENERATE_INTEL request for format: {format}", file=sys.stderr)

    if not format or not context:
        return {"success": False, "error": "Missing format or context for generation request."}

    # Basic context validation (ensure key parts exist)
    entity_info = context.get('entity')
    triggering_post = context.get('triggering_post')
    post_evaluation = context.get('post_evaluation')

    if not entity_info or not triggering_post or not post_evaluation:
         return {"success": False, "error": "Incomplete context provided for generation."}

    # --- 1. Formulate the AI Prompt --- #
    # This is crucial and needs refinement based on desired output quality.
    # Extract key info for easier use in prompt
    entity_name = entity_info.get('name', 'N/A')
    tweet_text = triggering_post.get('text', '[No Text]')
    sentiment = post_evaluation.get('sentiment_classification', 'N/A')
    sentiment_justification = post_evaluation.get('sentiment_justification', '')
    topics = ', '.join(post_evaluation.get('main_topics', [])) or 'N/A'

    prompt = f"""
You are an AI assistant for MAGA Operations, tasked with drafting political communications aligned with conservative principles and MAGA movement objectives.

**Target Entity:**
Name: {entity_name}
Type: {entity_info.get('type', 'N/A')}
Party: {entity_info.get('party', 'N/A')}
State: {entity_info.get('state', 'N/A')}
Twitter Handle: {entity_info.get('twitter_handle', 'N/A')}

**Triggering Tweet from {entity_name}:**
\"\"{tweet_text}\"\"

**AI Analysis of Tweet:**
Sentiment: {sentiment} ({sentiment_justification})
Main Topics: {topics}
Suggested Local Data Focus: {', '.join(post_evaluation.get('suggested_local_data', [])) or 'N/A'}

**Task:**
Draft a response in the format of a {format.upper()} based on the tweet and its analysis.

**Instructions for {format.upper()}:**
"""
    # Add refined format-specific instructions
    if format == 'email':
        prompt += f"""
- Write a concise internal email for the MAGA Operations team.
- Start with a clear subject line (e.g., "Intel Brief: Tweet from {entity_name}").
- Summarize the tweet's content and the AI's sentiment/topic analysis.
- Briefly suggest 1-2 potential strategic implications or opportunities based on the tweet (e.g., messaging alignment, counter-messaging needed).
- Maintain a professional, analytical, and objective tone suitable for internal comms.
"""
    elif format == 'post':
        prompt += f"""
- Draft a social media post (suitable for X/Twitter) that reacts to {entity_name}'s tweet.
- The tone should be assertive and align with MAGA principles. Reflect the tweet's sentiment ({sentiment}) appropriately (e.g., amplify if positive/aligned, critique if negative/opposed).
- Focus on one or two key topics ({topics}).
- Keep the post concise and impactful (under 280 characters if possible).
- Include 2-3 relevant hashtags (e.g., #MAGA, #SaveAmerica, or topic-specific like #BorderSecurity).
"""
    elif format == 'reply':
         prompt += f"""
- Draft a direct reply to {entity_name}'s tweet ({entity_info.get('twitter_handle', '')}).
- The tone should be direct and reflect the tweet's sentiment ({sentiment}) - either supportive or critical.
- Briefly address one specific point or topic ({topics}) from the original tweet or its analysis.
- Keep the reply very concise.
"""
    else: # Default/Fallback instructions
         prompt += f"""
- Generate a brief (1-2 sentence) summary or key talking point based on the tweet and its analysis.
- Capture the core message and sentiment.
"""

    print(f"Coordinator: Generated Prompt:\n{prompt[:500]}...", file=sys.stderr) # Log truncated prompt

    # --- 2. Call the AI --- #
    # For now, reuse the post_evaluator module's function, but ideally, this would be a dedicated generation function.
    # The existing function might not be ideal as it expects just the post text.
    # Let's adapt slightly - we'll pass the full prompt to the AI.
    # We might need to adjust `post_evaluator.py` or create a new function/module.
    
    # TEMPORARY: Assume post_evaluator can handle a full prompt string for generation
    # If post_evaluator.evaluate_post_with_ai only takes text, this needs change.
    try:
        print(f"Coordinator: Sending prompt to AI for generation...", file=sys.stderr)
        # --- This call signature might need to change --- #
        # Option A: Modify evaluate_post_with_ai to accept a full prompt
        # Option B: Create a new function e.g., generate_content(prompt)
        # For now, let's *assume* we can pass the prompt (will likely fail with current dummy)
        ai_result = post_evaluator.generate_response(prompt) # ASSUMING NEW FUNCTION or modified existing one
        # ------------------------------------------------ #

        if ai_result and ai_result.get('success') and ai_result.get('data'):
            generated_text = ai_result['data'].get('generated_text', '[AI failed to generate text]')
            print(f"Coordinator: Received generated text from AI.", file=sys.stderr)
            return {"success": True, "data": {"generated_text": generated_text}}
        else:
            error_msg = ai_result.get('error', 'AI generation failed or returned empty data.')
            print(f"Coordinator: AI generation failed: {error_msg}", file=sys.stderr)
            return {"success": False, "error": error_msg}

    except AttributeError:
         # Handle case where post_evaluator doesn't have generate_response
          print("Coordinator: ERROR - post_evaluator module does not have the expected generation function (e.g., generate_response). Need to implement it.", file=sys.stderr)
          return {"success": False, "error": "Backend AI generation function not implemented."}
    except Exception as e:
        print(f"Coordinator: Error during AI generation call: {e}", file=sys.stderr)
        return {"success": False, "error": f"AI generation failed: {e}"}

# --- NEW Search Request Handler ---
def handle_search_request(request_details):
    """Handles search requests for entities (politicians, influencers, etc.)."""
    query = request_details.get('query')
    logger.info(f"Handling SEARCH request for query: '{query}'")

    if not query:
        return {"success": False, "error": "Search query cannot be empty.", "timestamp": datetime.now().isoformat()}

    try:
        # --- Call the real database manager --- #
        search_results = database_manager.search_entities(query)
        # ---------------------------------------- #

        logger.info(f"Search completed for '{query}'. Returning {len(search_results)} results.")
        return {"success": True, "data": search_results, "source": "database_search"}

    except Exception as e:
        logger.exception(f"Error during search request for query '{query}'")
        return {"success": False, "error": f"Search failed: {e}", "timestamp": datetime.now().isoformat()}
# --- END Search Request Handler ---

# --- Main Request Router --- #
def route_request(request_data):
    """Routes the request to the appropriate handler based on the 'type'."""
    request_type = request_data.get('type')
    logger.debug(f"Routing request of type: {request_type}") # Use logger

    if request_type == 'fetch':
        return handle_fetch_request(request_data)
    elif request_type == 'evaluate_latest_post': # Changed from 'evaluate'
        return handle_evaluate_request(request_data)
    elif request_type == 'force_fetch':
        return handle_force_fetch_request(request_data)
    elif request_type == 'generate_intel':
        return handle_generate_intel_request(request_data)
    elif request_type == 'search': # Add case for search
        return handle_search_request(request_data) # Call the new handler
    else:
        logger.warning(f"Unknown request type: {request_type}") # Use logger
        return {
            "success": False,
            "error": f"Unknown request type: {request_type}",
            "timestamp": datetime.now().isoformat()
        }

# --- Main Execution Logic (if run directly or called from bridge) ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        request_json = sys.argv[1]
        try:
            request_data = json.loads(request_json)
            # Ensure background processor is running (might be needed for other tasks)
            start_background_processor()
            # Route the request to the appropriate handler
            result = route_request(request_data)
        except json.JSONDecodeError as e:
            result = {"success": False, "error": f"Invalid JSON input: {e}"}
        except Exception as e:
             result = {"success": False, "error": f"Coordinator script error: {e}"}

        print(json.dumps(result))
        # Decide on background thread management strategy later

    else:
        # --- Test Cases --- #
        print("Coordinator: No input provided. Running test cases.", file=sys.stderr)
        start_background_processor()

        # Test Case 1: Evaluate latest post
        print("\n--- Test Case: Evaluate Latest Post ---")
        test_eval_request = {
            "type": "evaluate_latest_post",
            "entity_type": "politician",
            "entity_id": "TestPolitician", # Dummy ID
            "context": {"twitter_handle": "elonmusk"} # Use a real handle for testing fetch
        }
        eval_result = route_request(test_eval_request)
        print(f"\nEvaluation Result (stdout):\n{json.dumps(eval_result, indent=2)}")

        # Test Case 2: Fetch data (which should queue background task)
        print("\n--- Test Case: Fetch (Missing) Data ---")
        test_fetch_request = {
            "type": "fetch",
            "entity_type": "influencer",
            "entity_id": "BennyJohnson",
            "field": "latest_videos"
        }
        fetch_result = route_request(test_fetch_request)
        print(f"\nFetch Result (stdout):\n{json.dumps(fetch_result, indent=2)}")

        print("\nCoordinator: Waiting a few seconds for potential background tasks...", file=sys.stderr)
        time.sleep(5)
        stop_background_processor()
        print("Coordinator: Test finished.", file=sys.stderr) 