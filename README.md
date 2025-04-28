# MAGA Operations - Political Intelligence Hub

## Core Purpose

The primary goal of MAGA Operations is to serve as an **AI-driven political intelligence hub**. It focuses on identifying, tracking, and **analyzing the relationships and interactions between key political figures (Politicians) and online commentators/public figures (Influencers)**. The application aims to synthesize data related to:

* Politician profiles, voting records, and public statements
* Influencer content, engagement metrics, and political positions
* Social media interactions between these entities
* Campaign finance data and political donations
* Voting patterns and legislative priorities

## Project Structure

```
MAGA_Ops/
├── config/                 # Configuration files
├── data/                   # Data storage and processing
├── scripts/                # Python scripts for data mining and processing
│   ├── data-mining/        # Scripts for collecting data from various sources
│   ├── db/                 # Database management scripts
│   ├── utils/              # Utility modules for common operations
│   │   ├── file_utils.py   # File operations and format handling
│   │   ├── string_utils.py # String manipulation and processing
│   │   ├── date_utils.py   # Date/time operations and formatting
│   │   ├── db_utils.py     # Database connection and operations
│   │   ├── config_utils.py # Configuration management
│   │   └── logger.py       # Logging configuration and utilities
├── src/                    # Electron application source code
│   ├── main/               # Main process code
│   ├── renderer/           # Renderer process code (UI)
│   ├── assets/             # Static assets (images, icons)
│   └── utils/              # Frontend utility functions
└── venv/                   # Python virtual environment
```

## Requirements

* [Node.js](https://nodejs.org/) v16+ and npm
* [Python](https://www.python.org/) 3.9+
* [Cursor IDE](https://cursor.sh/) - Currently required for development
* API keys for various services (Twitter, Google AI, etc.)

## Setup Instructions

### 1. Development Environment

This project is currently under active development and requires the [Cursor IDE](https://cursor.sh/) for proper functionality. Cursor provides enhanced AI-assisted coding features that are integrated with this project.

**[Download Cursor IDE here](https://cursor.sh/)**

### 2. Clone the Repository

```bash
git clone https://github.com/meeeeeooooowwwwwww/MAGA_Ops.git
cd MAGA_Ops
```

### 3. Set Up Python Environment

```bash
# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Set Up Node.js Environment

```bash
npm install
```

### 5. Configure Environment Variables

Create a `.env` file in the project root with the following content:

```
GOOGLE_API_KEY=your_google_ai_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
# Add other API keys as needed
```

### 6. Database Setup

The application uses SQLite for data storage. The database is automatically created when the application runs, but you can initialize it manually:

```bash
python scripts/db/initialize_db.py
```

### 7. Start the Application (Development Mode)

```bash
npm run dev
```

## Quick Setup for Beginners (Windows)

This section provides a simplified setup process for users on Windows who may be less familiar with development tools. This uses an automated script.

**Prerequisites:**

1.  **Git:** You need Git installed to download the project code. If you don't have it, download and install it from [git-scm.com](https://git-scm.com/download/win). During installation, accept the default settings.
2.  **Internet Connection:** Required to download dependencies.

**Steps:**

1.  **Download the Code:**
    *   Open **Git Bash** (which should have been installed with Git). You can find it in your Start Menu.
    *   Navigate to where you want to store the project (e.g., your Documents folder). You can use the `cd` command (e.g., `cd Documents`).
    *   Run the following command to download the project:
        ```bash
        git clone https://github.com/meeeeeooooowwwwwww/MAGA_Operations.git
        ```
    *   A folder named `MAGA_Operations` will be created. Close Git Bash.

2.  **Run the Setup Script:**
    *   Open File Explorer and navigate into the `MAGA_Operations` folder you just downloaded.
    *   Find the file named `setup.bat`.
    *   **Double-click `setup.bat`** to run it.
    *   A command prompt window will appear and show the progress. It will check for Python and Node.js, install all necessary software components (dependencies), and set up the initial database.
    *   **Important:** If the script asks for permission to install software or shows security warnings, you may need to approve them.
    *   The script will tell you if Python or Node.js are missing and provide links to install them. If this happens, install the missing software (accepting default settings is usually fine), then **run `setup.bat` again**.
    *   Wait for the script to finish. It will say "Setup Complete!" and pause.
You can close the window after reviewing any messages.

3.  **Configure API Keys (Optional but Recommended):**
    *   Inside the `MAGA_Operations` folder, find the file `.env.example`.
    *   Make a **copy** of this file and **rename the copy** to `.env` (just `.env`, with no file extension shown sometimes).
    *   Open the new `.env` file with a text editor (like Notepad).
    *   Follow the instructions inside the file to replace `"YOUR_GOOGLE_AI_API_KEY"` and `"YOUR_TWITTER_BEARER_TOKEN"` with your actual API keys. You need these for AI analysis and fetching recent tweets.
    *   Save and close the file.

4.  **Run the Application:**
    *   In the `MAGA_Operations` folder, find the file named `Run MAGA Ops` (this might be created by `npm start` or you might need to create a shortcut later - for now, use the command line if comfortable).
    *   *Alternatively, for now:* Open a Command Prompt (search for `cmd` in the Start Menu), navigate to the `MAGA_Operations` folder using `cd MAGA_Operations`, and run:
        ```bash
        npm start
        ```
    *   The application should launch.

**Troubleshooting:**

*   If the setup script fails, read the error messages carefully. They often indicate the problem (e.g., missing Python/Node, internet connection issue).
*   Ensure you have Python and Node.js added to your system's PATH environment variable if you installed them manually.
The installers usually offer an option to do this automatically.

## Utility Modules

The project includes several utility modules to streamline development:

### file_utils.py
- File operations (read/write)
- YAML, JSON, CSV handling
- File path management

### string_utils.py
- String normalization
- Text cleaning and formatting
- Pattern matching utilities

### date_utils.py
- Date parsing and formatting
- Time zone handling
- Date range operations

### db_utils.py
- SQLite database connections
- Transaction management
- Query execution utilities

### config_utils.py
- Configuration loading from various sources
- Environment variable management
- Application settings handling

### logger.py
- Configurable logging setup
- Log rotation and formatting
- Console and file logging

## Data Mining Framework

The data mining system consists of:

1. **Sources**: Modules that fetch data from external APIs and websites
2. **Processors**: Modules that analyze and transform the collected data
3. **Coordinator**: Central component managing the data mining workflow

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary and not licensed for public use.

## Status and Next Steps

Refer to [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) for detailed information about the current status of the project, recent changes, and planned next steps.

## Overview

This project is an Electron-based desktop application designed to function as the MAGA Operations **AI-driven** political intelligence hub. It integrates data tracking for **Politicians** and **Influencers**, enabling users to explore individual profiles and, crucially, **analyze the connections and interplay between these groups and related data points like funding and media activity.**

**The application leverages AI for two primary functions:**
1.  **Intelligence Generation:** Creating reports, social media drafts, email alerts, and other content based on user prompts and the integrated data.
2.  **Data Ecosystem Enhancement (Future Goal):** Assisting in the continuous improvement of the data foundation by identifying needs, suggesting schema/index changes, and potentially automating data acquisition from verified sources (FEC, official statements, etc.).

It combines a Node.js/Electron frontend with Python scripts for data scraping, processing, AI interaction, and database management.

## Recent Updates (Session Summary)

This session focused on restructuring the Python backend and implementing core data fetching capabilities:

1.  **Backend Restructure:**
    *   Introduced `scripts/api_bridge.py` as a simple, secure pass-through from Electron's `main.js` to the core Python logic.
    *   Centralized Python backend logic in `scripts/data-mining/coordinator.py`. This script now routes requests based on a `type` field in the JSON payload.
2.  **Database Implementation:**
    *   Created `scripts/db/database_manager.py` with a `DatabaseManager` class to handle SQLite interactions.
    *   Implemented methods for: 
        *   `search_entities(query)`: Searches `politicians` and `influencers` tables.
        *   `get_entity_field(entity_type, entity_id, field)`: Fetches a specific field for an entity.
        *   `update_entity_field(entity_type, entity_id, field, data)`: Updates a field, serializing list/dict to JSON.
        *   `get_relevant_entities(entity_type, reference_id)`: Placeholder for background tasks.
    *   The `coordinator.py` now imports and uses this real `DatabaseManager`, replacing previous dummy implementations.
3.  **Voting Records Source:**
    *   Added the `congress` library (`unitedstates/congress`) to `requirements.txt` to fetch official congressional data.
    *   Created `scripts/data-mining/sources/voting_records.py`.
    *   Implemented `fetch_recent_votes(entity_id, months_ago=24, max_votes=20)`: 
        *   Uses `subprocess` to run the `congress` library's command-line tool (`congress.run votes`) to download/update vote data into the `data/` directory.
        *   Parses the downloaded JSON vote files.
        *   Filters votes for the specified legislator (using Bioguide ID).
        *   Returns votes within the last `months_ago` (default 24) months, up to `max_votes`.
    *   The `coordinator.py` now imports and uses this source for `'voting_record'` field requests.
4.  **Search Functionality Integration:**
    *   Identified that the frontend search (`influencer-search.js`) was sending a `'search'` command not handled by the backend.
    *   Added routing for `'search'` in `coordinator.py` to call `handle_search_request`.
    *   Implemented `handle_search_request` to use `database_manager.search_entities` for querying the database.

## Features

*   **Main UI:** (Located in `src/renderer/index.html`, `renderer.js`, `styles.css`) Provides an interface likely focused on US legislators, potentially including search, details view, and tweet analysis (based on IPC handlers in `main.js`).
*   **Influencer Search UI:** (Located in `src/renderer/influencer-search.html`, `influencer-search.js`, `influencer-styles.css`) A dedicated interface for searching and exploring the influencer database. Features include:
    *   Keyword search for influencers (**Now connected to backend DB search**).
    *   Displaying top influencers (ranked by relevance).
    *   Browsing influencers by category or affiliation.
    *   Viewing detailed influencer profiles in a modal.
    *   Displaying an ideological distribution (basic bar chart).
*   **Entity Detail View:** (`src/renderer/entity-detail.html`, `.js`) Displays detailed information about a selected politician or influencer. Supports fetching and displaying:
    *   Base profile information.
    *   Politician Voting Records (**Now fetches last 24 months from official data**).
    *   Politician Committee Assignments (Placeholder).
    *   Influencer Metrics & Stances (Placeholders).
    *   Social Media (Twitter evaluation via AI placeholder).
    *   AI-driven content generation (email, post, reply drafts) based on context.
*   **Data Scraping:** Includes a Python script (`scripts/extract_influencers_full.py`) using Selenium to scrape influencer names from YouTube video titles (specifically configured for Benny Johnson's channel in previous versions).
*   **Python Backend Bridge:** An `api_bridge.py` script acts as an interface between the Electron frontend and the Python data logic (`coordinator.py`).
*   **Data Mining Coordinator (`coordinator.py`):** Central hub dispatching tasks for fetching data (voting records), database interaction (search, get/update fields), and AI processing (placeholders).
*   **Database Interaction (`database_manager.py`):** Manages connections and queries to the primary SQLite database (`maga_ops.db`).
*   **AI-Powered Generation:** Sidebar and profile actions trigger AI requests (currently placeholders or basic implementations) to generate reports, summaries, social media posts, etc., using available data context.
*   **AI-Driven Data Sourcing (Future Goal):** Planned capability for the AI to identify data needs, propose schema changes, and potentially manage data fetching/updates (as outlined in Future Enhancements).

## Setup and Installation

1.  **Clone the repository.**
2.  **Install Node.js dependencies:**
    ```bash
    cd MAGA_Ops
    npm install
    ```
3.  **Install Python dependencies:** Ensure you have Python 3 installed. Navigate to the `MAGA_Ops` directory and install required packages from `requirements.txt`:
    ```bash
    # Make sure you are in the MAGA_Ops directory
    pip install -r requirements.txt 
    ```
4.  **Set up the Database (`maga_ops.db`):**
    *   Ensure the SQLite database file exists in the project root.
    *   Verify it contains `politicians` and `influencers` tables with appropriate columns (see `database_manager.py` for columns used in search).
    *   *Note: The previous `setup-db.js` and `politicians.db` may be deprecated or need merging into `maga_ops.db`.*

## Running the Application

*   **Development Mode (with DevTools):**
    ```bash
    cd MAGA_Ops
    npm run dev
    ```
*   **Standard Mode:**
    ```bash
    cd MAGA_Ops
    npm start
    ```

## Directory Structure Overview

```
MAGA_Ops/
├── .circleci/        
├── cache/
│   └── congress/     # Cache for unitedstates/congress tool downloads
├── data/             # Contains downloaded data from sources (e.g., congress tool)
├── node_modules/     
├── scripts/          
│   ├── api_bridge.py # Simple entry point calling coordinator.py
│   ├── data-mining/  # Handles external data fetching, processing, and AI analysis
│   │   ├── __init__.py
│   │   ├── coordinator.py # Central dispatcher for data mining/evaluation tasks
│   │   ├── sources/       # Modules for specific data sources
│   │   │   ├── __init__.py
│   │   │   ├── voting_records.py # Fetches votes via unitedstates/congress tool
│   │   │   └── ... (twitter_profile.py, committees.py - placeholders)
│   │   ├── processors/    # Modules for processing/analyzing data (AI)
│   │   │   ├── __init__.py
│   │   │   ├── post_evaluator.py # Placeholder/Dummy AI analysis
│   │   │   └── ...
│   │   └── utils/         # Shared utilities 
│   │       └── logging_config.py 
│   ├── db/           # Database interaction logic
│   │   ├── __init__.py
│   │   └── database_manager.py # Manages SQLite connection and queries
│   └── ...           # Other utility scripts (e.g., old scraper)
├── src/              # Source code for the Electron application
│   ├── main/         
│   │   └── main.js   # Main Electron process 
│   ├── renderer/     # UI code (HTML, CSS, JS)
│   │   └── ...
│   ├── services/     # (Likely deprecated by python bridge)
│   ├── utils/        
│   └── preload.js    # Electron preload script
├── test/             
├── venv/             # Python virtual environment (if used)
├── .env              # Environment variables (e.g., API keys - *KEEP SECRET*)
├── .gitignore        
├── .stylelintrc.json 
├── console.log.txt   # Log file for main process output
├── maga_ops.db       # Primary SQLite database
├── package.json      
├── package-lock.json 
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Core Components & Data Flow

*   **Electron (`src/main/main.js`, `src/preload.js`):** Manages the application window, lifecycle, and defines secure IPC channels (like `python-bridge`) exposed via `preload.js`.
*   **Renderer UI (`src/renderer/`):** HTML, CSS, and JavaScript files defining the user interfaces. Uses `window.electronAPI.invoke('python-bridge', json_payload)` via the preload script to send requests to the main process.
*   **IPC Handling (`main.js`):** The main process listens for IPC requests on the `python-bridge` channel. When a request is received, it spawns the `api_bridge.py` script, passing the JSON payload string as an argument.
*   **Python Bridge (`scripts/api_bridge.py`):** Acts as a simple, secure entry point. It receives the JSON request string, executes the `coordinator.py` script with this argument using `subprocess`, captures the coordinator's standard output (which should be a JSON response string), and prints this response back to the main Electron process.
*   **Data Mining Coordinator (`scripts/data-mining/coordinator.py`):** The central hub for Python operations. Parses the incoming JSON request, determines the action (`search`, `fetch`, `evaluate_latest_post`, `force_fetch`, `generate_intel`), calls appropriate functions in `sources/`, `processors/`, or `db/database_manager.py`, and formats the final JSON response.
*   **Database Manager (`scripts/db/database_manager.py`):** Handles all SQLite interactions (connecting, searching, getting/setting fields).
*   **Data Sources (`scripts/data-mining/sources/`):** Modules responsible for fetching data from external sources. `voting_records.py` uses the `unitedstates/congress` tool.
*   **Data Processors (`scripts/data-mining/processors/`):** Modules responsible for analyzing or transforming data, often involving AI (currently placeholders).

## Development Notes

*   **Logging:** All `console.log`, `console.error`, uncaught exceptions, and unhandled rejections from the main process are logged to `MAGA_Ops/console.log.txt`. Python scripts use the standard `logging` module, configured via `utils/logging_config.py`.
*   **Styling:** CSS is linted using Stylelint (`.stylelintrc.json`).
*   **Database:** The primary database is now intended to be `maga_ops.db` in the project root.
*   **Bioguide IDs:** Fetching voting records requires the legislator's Bioguide ID. Ensure this ID is available and passed correctly when requesting politician data.

## Data Work / Jobs Tasks

*   **Fetch Older Voting Records:** The current `voting_records.py` fetches data for the last ~24 months. A background process could be implemented later to run `congress.run votes --congress=<number>` for older Congresses to populate historical vote data.
*   **Implement Remaining Data Sources:** Create real implementations for `committees.py`, `twitter_profile.py`, `fec_lookup.py`, `influencer_metrics.py`, `influencer_stances.py`, etc., replacing the current dummies.
*   **Implement AI Processors:** Replace dummy AI functions in `post_evaluator.py` and for `generate_intel` with actual calls to AI models.
*   **Database Schema/Migration:** Define and manage the schema for `maga_ops.db`, potentially merging data from older DBs.
*   **Background Task Enrichment:** Fully implement the background task logic in `coordinator.py` and the `get_relevant_entities` method in `database_manager.py` for data enrichment.

## Future Enhancements (Ideas)

*   **Implement AI-Driven Data Sourcing:** Fully realize the system where the AI can:
    *   Identify when requested data (e.g., specific connections, recent funding) is missing.
    *   Log these "data needs".
    *   Propose or automatically implement database schema changes (new tables/columns, indices).
    *   Generate/run scraping/API scripts to fetch and populate the missing data from verified sources.
    *   Update database documentation (e.g., a `data_sources.md` file) automatically.
    *   Track the provenance and freshness of data.
*   **Expand Generation Capabilities:** Add more sophisticated report types, allow complex multi-entity analysis prompts.
*   **Refine Data:** Clean up noise and improve data quality in the influencer/politician databases.
*   **Improve UI:** Enhance visualizations, improve modal details, add more robust error handling for AI interactions.

## Database Schema and Entity Categorization

### Overview

MAGA_Ops uses a normalized SQLite database design to efficiently store and relate Politicians and Influencers while sharing common categorization types (party affiliation, ideology, Trump stance, etc.).

The database follows these design principles:
- **Entity-based architecture** with base entity table and specialized extensions
- **Flexible categorization system** using a type-category-relation pattern
- **Relationship tracking** between entities
- **Proper indexing** for performance optimization
- **View-based queries** for common data access patterns

### Core Data Structure

The database is organized around these primary concepts:

1. **Entities**: Base table for all tracked individuals/organizations
2. **Entity Types**: Politicians and Influencers extend the base entity
3. **Categories**: Shared classification system (party, ideology, etc.)
4. **Relationships**: Connections between entities
5. **Content**: Social posts, voting records, and other entity-specific data

### Schema Diagram

```
┌─────────────┐       ┌──────────────┐        ┌───────────────┐
│   entities  │───1:1─┤  politicians │        │ category_types │
├─────────────┤       ├──────────────┤        ├───────────────┤
│ id          │       │ entity_id    │        │ id            │
│ name        │       │ office       │        │ name          │
│ bio         │       │ state        │        │ description   │
│ entity_type │       │ district     │        │ is_multiple   │
└──────┬──────┘       └──────────────┘        └───────┬───────┘
       │                                              │
       │              ┌──────────────┐                │
       └──────1:1─────┤  influencers │                │
       │              ├──────────────┤                │
       │              │ entity_id    │                │
       │              │ platform     │                │
       │              │ audience_size│                │
       │              └──────────────┘                │
       │                                              │
       │              ┌─────────────────┐             │
       │              │entity_connections│             │
       └──────M:N─────┼─────────────────┼───M:N───────┘
       │              │ entity1_id      │             │
       │              │ entity2_id      │             │
       │              │ connection_type │             │
       │              └─────────────────┘             │
       │                                              │
       │              ┌─────────────┐                 │
       │              │  categories │                 │
       └──────M:N─────┼─────────────┼────M:1──────────┘
                      │ id          │
                      │ category_type_id │
                      │ code        │
                      │ name        │
                      └─────────────┘
```

### Entity Categories

The categorization system is flexible and hierarchical:

1. **Category Types**: Meta-categories like 'party', 'ideology', 'entity_type'
2. **Categories**: Specific values within each type (e.g., 'REPUBLICAN', 'DEMOCRAT', 'MAGA')
3. **Entity-Category Relations**: M:N relationships between entities and categories

This design allows for:
- Different entity types to share the same category values
- Some categories to support multiple values per entity (e.g., ideologies)
- Others to enforce single values (e.g., party affiliation)
- AI-assigned confidence scores for each categorization

### Entity Relationships

The database tracks connections between entities with:
- Directional relationships (entity1 → entity2)
- Connection types (mentions, endorses, opposes)
- Strength scores (0-1 scale)
- Evidence sources

### Setup and Migration

The database setup process has been improved with:

1. **Schema Creation**: Using `scripts/db/schema.sql` for table definitions
2. **Data Migration**: `scripts/db/migrate_data.py` to move data from old to new schema
3. **Initialization**: `scripts/db/initialize_db.py` to setup a new database or update existing

To initialize or update the database:

```bash
# Create logs directory if it doesn't exist
mkdir -p logs

# Run the initialization script
python scripts/db/initialize_db.py
```

### Database Access

Database interactions are handled through the `DatabaseManager` class:

```python
from scripts.db.database_manager import DatabaseManager

# Create an instance
db = DatabaseManager()

# Search for entities
results = db.search_entities("trump", entity_type="politician")

# Get a specific entity with categories
entity = db.get_entity(123)

# Get entities by category
maga_entities = db.get_entities_by_category("MAGA")

# Update entity fields
db.update_entity_field("politician", 123, "state", "Florida")

# Add a category to entity
db.update_entity_field("influencer", 456, "category_ideology", "MAGA")
```

The manager provides methods for all common database operations.
