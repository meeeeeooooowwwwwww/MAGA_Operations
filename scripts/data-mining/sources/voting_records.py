import os
import subprocess
import json
import logging
from datetime import datetime, timedelta
import glob
import sys # Needed for sys.executable

logger = logging.getLogger(__name__)

# Determine project root assuming this script is in scripts/data-mining/sources
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CONGRESS_DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
CONGRESS_CACHE_DIR = os.path.join(PROJECT_ROOT, 'cache', 'congress') # Specific cache for congress tool

# Ensure cache directory exists
os.makedirs(CONGRESS_CACHE_DIR, exist_ok=True)

def run_congress_tool(force_update=False):
    """Runs the 'usc-run votes' command to download/update vote data."""
    # Construct command using sys.executable
    usc_run_path = os.path.join(os.path.dirname(sys.executable), 'usc-run') # Try to find usc-run in same dir as python
    if not os.path.exists(usc_run_path):
        usc_run_path = 'usc-run' # Fallback to assuming it's in PATH
        
    command = [usc_run_path, 'votes', '--cachedir', CONGRESS_CACHE_DIR, '--datadir', CONGRESS_DATA_DIR]
    if force_update:
        command.append('--force')
        logger.info("Forcing update of congress vote data.")
    else:
        logger.info("Running congress tool to update vote data (using cache if possible).")

    try:
        # Use sys.executable to ensure using the same python env where 'congress' was installed
        # Run from project root context
        # Using sys.executable directly might be more reliable than finding usc-run separately
        process = subprocess.run([sys.executable, '-m', 'congress.run', 'votes', '--cachedir', CONGRESS_CACHE_DIR, '--datadir', CONGRESS_DATA_DIR] + (['--force'] if force_update else []),
                                 capture_output=True, text=True, check=False,
                                 cwd=PROJECT_ROOT)

        if process.returncode != 0:
            logger.error(f"congress.run votes failed with code {process.returncode}.")
            logger.error(f"Stderr: {process.stderr}")
            logger.error(f"Stdout: {process.stdout}")
            return False
        else:
            logger.info("congress.run votes completed successfully.")
            # Log stdout for potential info messages from the tool
            if process.stdout:
                 logger.debug(f"congress.run votes stdout: {process.stdout[:500]}...") # Log first 500 chars
            if process.stderr: # Also log stderr in case of warnings
                 logger.warning(f"congress.run votes stderr: {process.stderr[:500]}...")
            return True

    except FileNotFoundError:
        logger.exception("Python executable not found or congress module not installed correctly.")
        return False
    except Exception as e:
        logger.exception(f"An error occurred while running congress.run votes: {e}")
        return False

def fetch_recent_votes(entity_id, months_ago=24, max_votes=20):
    """Fetches roll call votes for a specific legislator within the last N months.

    Args:
        entity_id (str): The Bioguide ID of the legislator.
        months_ago (int): How many months back to fetch votes for (default 24).
        max_votes (int): Maximum number of recent votes to return within the time window.

    Returns:
        dict: A dictionary with 'success' (bool) and 'data' (list of votes) or 'error' (str).
    """
    logger.info(f"Fetching votes from last {months_ago} months for legislator Bioguide ID: {entity_id}")

    # 1. Ensure data is up-to-date
    if not run_congress_tool():
        return {"success": False, "error": "Failed to run congress data tool to update votes."}

    # 2. Determine time window and relevant sessions
    cutoff_date = datetime.now() - timedelta(days=months_ago * 30.5) # Approximate months
    relevant_vote_files = []

    try:
        # Iterate through congress directories (e.g., data/118, data/117)
        congress_dirs = sorted([d for d in os.listdir(CONGRESS_DATA_DIR) if d.isdigit()], key=int, reverse=True)
        if not congress_dirs:
            return {"success": False, "error": f"No Congress data found in {CONGRESS_DATA_DIR}"}

        for congress_num in congress_dirs:
            congress_votes_dir = os.path.join(CONGRESS_DATA_DIR, congress_num, 'votes')
            if not os.path.isdir(congress_votes_dir):
                continue

            # Iterate through session directories (e.g., 2023, 2024 or 118)
            session_dirs = sorted([d for d in os.listdir(congress_votes_dir)], reverse=True)
            for session_id in session_dirs:
                session_path = os.path.join(congress_votes_dir, session_id)
                if not os.path.isdir(session_path):
                    continue
                
                # Basic check: If session ID is a year, check if it's recent enough
                try:
                    session_year = int(session_id)
                    if session_year < cutoff_date.year - 1: # Check if session year is too old
                        # Optimization: Stop searching older congresses/sessions if this one is too old
                        # This assumes sessions are primarily year-based
                        # logger.debug(f"Skipping older session {session_id} (before {cutoff_date.year - 1})\")
                        # break # Break from session loop for this congress
                        # Let's process all files first and filter by date later for simplicity now
                        pass 
                except ValueError:
                    # Handle non-year session IDs if necessary (e.g., '118')
                    pass 

                # Find all json files within this session
                # Pattern: data/<congress>/votes/<session>/<chamber>/<vote_num>/data.json
                session_vote_glob = os.path.join(session_path, '\*/*/*.json')
                session_files = glob.glob(session_vote_glob)
                relevant_vote_files.extend(session_files)
        
        if not relevant_vote_files:
             return {"success": False, "error": "No vote data files found in any session."}
             
        logger.debug(f"Found {len(relevant_vote_files)} total vote files to potentially process.")

        # 3. Sort all found files by date (descending) then parse and filter
        def get_vote_file_metadata(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                vote_date_str = data.get('date')
                vote_date = datetime.fromisoformat(vote_date_str) if vote_date_str else datetime.min
                vote_num = int(os.path.basename(os.path.dirname(filepath))) # Use vote num as secondary sort key
                return {'path': filepath, 'date': vote_date, 'vote_num': vote_num}
            except Exception as e:
                logger.warning(f"Failed to read metadata from {filepath}: {e}", exc_info=True)
                return {'path': filepath, 'date': datetime.min, 'vote_num': -1}

        # Get metadata and filter out files that failed to read
        file_metadata = [get_vote_file_metadata(f) for f in relevant_vote_files]
        valid_files_metadata = [m for m in file_metadata if m['date'] > datetime.min]
        
        # Sort by date (most recent first), then vote number (highest first)
        valid_files_metadata.sort(key=lambda x: (x['date'], x['vote_num']), reverse=True)

        logger.debug(f"Processing {len(valid_files_metadata)} valid vote files, sorted by date.")

        # 4. Parse files within the time window and extract relevant votes
        member_votes = []
        processed_files = 0
        for meta in valid_files_metadata:
            # Stop if we have enough votes
            if len(member_votes) >= max_votes:
                 break
            
            # Stop if the vote date is older than the cutoff
            if meta['date'] < cutoff_date:
                continue

            processed_files += 1
            vote_file = meta['path']
            try:
                # Re-read the file (or pass data from metadata step if memory allows)
                with open(vote_file, 'r', encoding='utf-8') as f:
                    vote_data = json.load(f)

                # Check if this member participated in this vote
                member_vote_position = None
                if 'votes' in vote_data:
                     for position, voters in vote_data['votes'].items():
                          for voter in voters:
                              if voter.get('id') == entity_id:
                                   member_vote_position = position
                                   break 
                          if member_vote_position:
                               break 

                if member_vote_position:
                    # Format the vote information
                    vote_info = {
                        "vote_id": vote_data.get('vote_id'),
                        "chamber": vote_data.get('chamber'),
                        "session": vote_data.get('session'),
                        "roll_number": vote_data.get('number'),
                        "date": vote_data.get('date'),
                        "question": vote_data.get('question'),
                        "description": vote_data.get('description'),
                        "result": vote_data.get('result'),
                        "bill_number": vote_data.get('bill', {}).get('number') if vote_data.get('bill') else None,
                        "bill_title": vote_data.get('bill', {}).get('title') if vote_data.get('bill') else None,
                        "member_position": member_vote_position,
                        "vote_type": vote_data.get('type')
                    }
                    member_votes.append(vote_info)

            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON from vote file: {vote_file}")
            except Exception as e:
                logger.exception(f"Error processing vote file {vote_file}: {e}")

        logger.info(f"Found {len(member_votes)} votes within the last {months_ago} months for {entity_id} after processing {processed_files} relevant files.")
        return {"success": True, "data": member_votes}

    except Exception as e:
        logger.exception(f"An error occurred trying to find or parse vote files for {entity_id}: {e}")
        return {"success": False, "error": f"Failed to process vote data files: {e}"}

# Example Usage (for testing this script directly)
if __name__ == '__main__':
    # Add parent dir to path to allow importing logging_config
    # This assumes coordinator.py is in ../ relative to sources/
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir) 
    try:
        from utils.logging_config import setup_logging
        setup_logging(log_level=logging.DEBUG)
    except ImportError:
         print("Could not import logging_config. Using basic logging.")
         logging.basicConfig(level=logging.DEBUG)

    # Replace with a valid Bioguide ID of a current legislator for testing
    test_bioguide_id = 'P000197' # Example: Pelosi
    print(f"Testing fetch_recent_votes (last 24 months) for Bioguide ID: {test_bioguide_id}")
    
    result = fetch_recent_votes(test_bioguide_id, months_ago=24)
    
    if result['success']:
        print(f"Successfully fetched {len(result['data'])} votes.")
        if result['data']:
             print("Most recent vote found:")
             print(json.dumps(result['data'][0], indent=2))
        else:
            print("No recent votes found for this legislator in the parsed files within the time window.")
    else:
        print(f"Error fetching votes: {result['error']}")