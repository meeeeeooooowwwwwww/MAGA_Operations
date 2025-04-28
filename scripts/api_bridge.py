#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API Bridge for MAGA Ops (Refactored)

This script acts as a simple entry point for requests from Electron.
It takes a single JSON string as a command-line argument, passes it 
to the data mining coordinator script, captures the JSON response from
the coordinator's stdout, and prints it back to the caller (Electron).
"""

import sys
import os
import subprocess
import json
from datetime import datetime

def main():
    # Expecting one argument: the JSON request string
    if len(sys.argv) != 2:
        error_response = json.dumps({
            "success": False,
            "error": "API Bridge expects exactly one argument (JSON request string).",
            "timestamp": datetime.now().isoformat() # Include timestamp for consistency
        })
        print(error_response)
        sys.exit(1)

    json_request_string = sys.argv[1]

    # Validate if the input is at least plausibly JSON
    try:
        json.loads(json_request_string)
    except json.JSONDecodeError as e:
        error_response = json.dumps({
            "success": False,
            "error": f"Invalid JSON request string provided to API Bridge: {e}",
            "timestamp": datetime.now().isoformat()
        })
        print(error_response)
        sys.exit(1)

    # Determine the path to the coordinator script relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    coordinator_path = os.path.join(script_dir, "data-mining", "coordinator.py")

    if not os.path.exists(coordinator_path):
         error_response = json.dumps({
            "success": False,
            "error": f"Coordinator script not found at: {coordinator_path}",
            "timestamp": datetime.now().isoformat()
        })
         print(error_response)
         sys.exit(1)

    try:
        # Execute the coordinator script using the same Python interpreter
        # Pass the JSON request string as a command-line argument
        # Capture stdout, stderr; decode stdout as UTF-8
        process = subprocess.run(
            [sys.executable, coordinator_path, json_request_string],
            capture_output=True,
            text=True, # Decodes stdout/stderr using default encoding (usually utf-8)
            check=False, # Don't raise exception on non-zero exit code, handle below
            cwd=os.path.dirname(script_dir) # Run from the parent (MAGA_Ops) directory context if needed for paths in coordinator
        )

        # Print coordinator's stderr for debugging purposes (visible in Electron's console)
        if process.stderr:
            print(f"Coordinator stderr:\n{process.stderr}", file=sys.stderr)

        # Check coordinator's exit code
        if process.returncode != 0:
            error_response = json.dumps({
                "success": False,
                "error": f"Coordinator script exited with error code {process.returncode}. See stderr log.",
                "coordinator_stdout": process.stdout.strip(), # Include stdout in case it holds partial error info
                "timestamp": datetime.now().isoformat()
             })
            print(error_response)
        else:
            # Assume coordinator's stdout is the JSON response we need
            # Minimal validation: check if it's empty
            coordinator_response = process.stdout.strip()
            if not coordinator_response:
                 error_response = json.dumps({
                    "success": False,
                    "error": "Coordinator script produced empty output.",
                    "timestamp": datetime.now().isoformat()
                 })
                 print(error_response)
            else:
                 # Attempt to parse coordinator output to ensure it's valid JSON before returning
                 try:
                     json.loads(coordinator_response)
                     # Success! Print the coordinator's valid JSON response directly to our stdout
                     print(coordinator_response)
                 except json.JSONDecodeError as json_err:
                     error_response = json.dumps({
                        "success": False,
                        "error": f"Coordinator script output was not valid JSON: {json_err}",
                        "coordinator_raw_output": coordinator_response,
                        "timestamp": datetime.now().isoformat()
                     })
                     print(error_response)

    except Exception as e:
        # Catch errors during subprocess execution itself
        error_response = json.dumps({
            "success": False,
            "error": f"Failed to execute coordinator script: {e}",
            "timestamp": datetime.now().isoformat()
        })
        print(error_response)
        sys.exit(1)

if __name__ == "__main__":
    main() 