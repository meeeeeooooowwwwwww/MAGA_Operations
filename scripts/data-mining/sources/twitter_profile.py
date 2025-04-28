# Twitter Profile Data Fetching 

import os
import tweepy
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env file located in the project root
# Go up three levels from current file (sources -> data-mining -> scripts -> MAGA_Ops)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
dotenv_path = os.path.join(project_root, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    # print(f"Loaded .env from: {dotenv_path}", file=sys.stderr) # Optional debug
else:
    print(f"Warning: .env file not found at {dotenv_path}", file=sys.stderr)

# Get Twitter Bearer Token from environment variables
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# --- Tweepy Client Initialization ---
# Initialize outside the function to potentially reuse the client
# Check if the token was loaded
if not TWITTER_BEARER_TOKEN:
    print("Error: TWITTER_BEARER_TOKEN not found in environment variables.", file=sys.stderr)
    # Set client to None so functions can check and fail gracefully
    client = None
else:
    try:
        # Use tweepy.Client for API v2
        client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=True)
        print("Twitter client initialized successfully.", file=sys.stderr) # Debug
    except Exception as e:
        print(f"Error initializing Tweepy client: {e}", file=sys.stderr)
        client = None

# --- Fetch Function ---
def fetch_latest_tweet(twitter_handle: str) -> dict:
    """
    Fetches the latest original tweet (no retweets/replies) for a given Twitter handle.

    Args:
        twitter_handle: The Twitter screen name (without '@').

    Returns:
        A dictionary containing {'id': tweet_id, 'text': tweet_text, 'timestamp': fetch_time}
        or {'error': error_message} if an error occurs.
    """
    if client is None:
        return {"success": False, "error": "Twitter client not initialized. Check API keys."}

    if not twitter_handle:
        return {"success": False, "error": "Twitter handle cannot be empty."}

    print(f"TWITTER_FETCH: Attempting to fetch latest tweet for handle: {twitter_handle}", file=sys.stderr)

    try:
        # 1. Get user ID from handle
        print(f"TWITTER_FETCH: Getting user ID for {twitter_handle}...", file=sys.stderr)
        user_response = client.get_user(username=twitter_handle)

        if user_response.errors:
             error_detail = user_response.errors[0].get('detail', 'Unknown error')
             print(f"TWITTER_FETCH Error (get_user): {error_detail}", file=sys.stderr)
             return {"success": False, "error": f"Could not find Twitter user '{twitter_handle}': {error_detail}"}

        if not user_response.data:
             print(f"TWITTER_FETCH Error: No user data returned for {twitter_handle}", file=sys.stderr)
             return {"success": False, "error": f"Could not find Twitter user '{twitter_handle}' (no data)."}

        user_id = user_response.data.id
        print(f"TWITTER_FETCH: Found user ID: {user_id} for {twitter_handle}", file=sys.stderr)

        # 2. Get the latest tweet(s) - max_results=5 is minimum for v2 timeline endpoint
        # Exclude retweets and replies to get original posts
        print(f"TWITTER_FETCH: Getting tweets for user ID: {user_id}...", file=sys.stderr)
        tweet_response = client.get_users_tweets(
            id=user_id,
            max_results=5, # Fetch 5, take the first one
            exclude=['retweets', 'replies']
        )

        if tweet_response.errors:
             error_detail = tweet_response.errors[0].get('detail', 'Unknown error')
             print(f"TWITTER_FETCH Error (get_users_tweets): {error_detail}", file=sys.stderr)
             return {"success": False, "error": f"Error fetching tweets for '{twitter_handle}': {error_detail}"}

        if not tweet_response.data:
            print(f"TWITTER_FETCH: No original tweets found for {twitter_handle}.", file=sys.stderr)
            return {"success": False, "error": f"No recent original tweets found for '{twitter_handle}'."}

        # 3. Extract the latest tweet
        latest_tweet = tweet_response.data[0]
        fetch_timestamp = time.time()

        print(f"TWITTER_FETCH: Successfully fetched latest tweet ID: {latest_tweet.id}", file=sys.stderr)
        return {
            "success": True,
            "data": {
                "id": str(latest_tweet.id), # Ensure ID is string
                "text": latest_tweet.text,
                "timestamp": fetch_timestamp
            }
        }

    except tweepy.errors.TweepyException as e:
        print(f"TWITTER_FETCH Tweepy Error: {e}", file=sys.stderr)
        return {"success": False, "error": f"Twitter API error: {e}"}
    except Exception as e:
        # Catch any other unexpected errors
        print(f"TWITTER_FETCH Unexpected Error: {e}", file=sys.stderr)
        return {"success": False, "error": f"An unexpected error occurred: {e}"}

# --- Example Usage (if run directly) ---
if __name__ == "__main__":
    # Example handles to test
    test_handles = ["elonmusk", "JoeBiden", "InvalidUserXYZ123", "POTUS"] # Add a known handle

    if client: # Only run if client initialized
        for handle in test_handles:
            print(f"\n--- Testing handle: {handle} ---")
            result = fetch_latest_tweet(handle)
            print(f"Result for {handle}: {result}\n")
            time.sleep(1) # Small delay between tests
    else:
        print("\nCould not run tests: Twitter client failed to initialize.")

    print("--- Twitter Profile Script Finished ---") 