# MAGA Ops - Project Context & Status

**IMPORTANT NOTE: Active Development & User Responsibility**

This application is under **active and rapid development**. Updates may occur frequently (potentially hourly/daily). While we strive for stability, you may encounter bugs, incomplete features, or require adjustments after pulling updates.

Users are expected to leverage **[Cursor IDE's](https://cursor.sh/) AI capabilities** to assist with potential setup issues, understanding recent code changes, or adapting parts of the application as needed.

**By using this application, you acknowledge its developmental nature and accept all risks and responsibilities associated with its use.** The developers provide this tool as-is, without warranties. Please ensure you regularly pull the latest changes from the GitHub repository (`git pull origin main`) before starting work.

---

**Last Updated:** May 2, 2025

**Objective:** To provide a snapshot of the current project architecture, recent changes, and immediate next steps, supplementing the main README.md.

## Recent Major Updates

### 1. Comprehensive Utility Module Framework

We have implemented a robust utility framework to streamline development and ensure code consistency:

- **`file_utils.py`**: Comprehensive file operations with support for multiple formats (YAML, JSON, CSV)
- **`string_utils.py`**: String manipulation utilities for text normalization, cleaning, and pattern matching
- **`date_utils.py`**: Date/time operations with timezone handling and formatting capabilities
- **`db_utils.py`**: Database utilities with transaction support and connection management
- **`config_utils.py`**: Configuration management from various sources (files, environment variables)
- **`logger.py`**: Centralized logging system with configurable outputs

These utilities are now accessible via the `scripts.utils` package through the newly created `__init__.py` file.

### 2. Development Environment Standardization

The project now requires [Cursor IDE](https://cursor.sh/) for development, providing AI-assisted coding features integrated with our workflow. This decision was made to enhance productivity and maintain code quality standards.

### 3. Documentation Improvements

We have significantly improved project documentation:

- Updated README.md with comprehensive project structure and setup instructions
- Enhanced inline code documentation with type hints and example usage
- Standardized docstring format across all new utility modules

### 4. Enhanced Data Processing & AI Integration

Significant progress has been made in data handling and analysis:

- **Database Schema Refinement:** The core database schema (`scripts/db/schema.sql`) has been substantially updated to accommodate diverse entity types (Politicians, Influencers), relationships, social media posts, stances, and AI-generated metadata. Key tables include `entities`, `entity_metadata`, `social_media_posts`, `political_stances`, `relationships`, `financial_disclosures`, and `ai_analysis_log`.
- **AI-Powered Post Evaluation:** Implemented `scripts/data-mining/processors/post_evaluator.py` utilizing Google's Gemini API (`gemini-1.5-flash-latest`) for:
    - Sentiment analysis (Positive, Negative, Neutral, Assertive, etc.) with justification.
    - Extraction of key political/social topics.
    - Suggestion of relevant local data points for contextual understanding.
    - Robust error handling and structured JSON output.
- **Data Mining Coordinator:** The `scripts/data-mining/coordinator.py` script acts as the central hub for Python backend operations, routing requests from the Electron frontend (via `scripts/api_bridge.py`) to appropriate data sources and processors. It handles request parsing, orchestrates data fetching (e.g., latest tweets via `scripts/data-mining/sources/twitter_profile.py`) and AI analysis, and manages basic threading for background tasks.
- **New Data Sources & Scripts:** Added initial implementations or structures for various data sources (e.g., `fec_lookup.py`, `youtube_channel.py`, `committees.py`) and processing scripts (`entity_linker.py`, `sentiment_basic.py`, `generate_influencers.py`).
- **Database Management:** Enhanced database utility scripts (`scripts/db/`) including `initialize_db.py`, `database_manager.py`, `import_entities.py`, and schema checking/migration tools.

### 5. Frontend Refactoring: Generic Entity View

Refactored the frontend to use a generic `entity-detail.html` and `entity-detail.js` for displaying information about any entity type, replacing separate views for politicians and influencers. This improves scalability and reduces code duplication.

## Current Architecture

```
MAGA_Ops/
├── config/                # Configuration files (data_mining.yaml, etc.)
├── data/                  # Local data storage (cached files, potentially DB backups)
├── logs/                  # Log files
├── scripts/               # Python backend scripts & utilities
│   ├── data-mining/       # Data collection & processing framework
│   │   ├── sources/       # API integrations & web scrapers (Twitter, FEC, YouTube...)
│   │   ├── processors/    # Data transformation & analysis (AI eval, linking...)
│   │   └── utils/         # Shared utilities for data mining (API, cache, DB...)
│   ├── db/                # Database management (schema, initialization, import...)
│   ├── utils/             # Core shared utility modules (files, dates, strings...)
│   └── api_bridge.py      # Interface between Electron main process and Python coordinator
├── src/                   # Electron application source
│   ├── main/              # Main process logic (main.js, preload.js)
│   └── renderer/          # User interface (HTML, CSS, JS - React Planned)
├── .env                   # Environment variables (API keys, etc.)
├── maga_ops.db            # Main SQLite database file (IGNORED by git)
└── ...                    # Other config files (.gitignore, package.json, etc.)
```

## Development Status

### Completed
- ✅ Core utility module framework (`scripts/utils/`)
- ✅ Basic project structure & configuration (`config/`, `.env`)
- ✅ Documentation framework (`README.md`, `PROJECT_CONTEXT.md`)
- ✅ Initial Database Schema (`scripts/db/schema.sql`) & setup scripts
- ✅ Core Data Mining Coordinator (`scripts/data-mining/coordinator.py`)
- ✅ Python-Electron Bridge (`scripts/api_bridge.py`, `main.js` integration)
- ✅ Twitter Profile Fetching (`scripts/data-mining/sources/twitter_profile.py`)
- ✅ AI Post Evaluation (`scripts/data-mining/processors/post_evaluator.py`)
- ✅ Generic Entity Detail View (Frontend Refactor - `entity-detail.html`/`.js`)
- ✅ Git repository setup and initial push

### In Progress
- 🔄 **Database Integration:** Replacing dummy DB calls in `coordinator.py` with actual `scripts/db/database_manager.py` interactions.
- 🔄 **Frontend Implementation (`entity-detail.js`):** Fully implementing data display, tab functionality, and interaction logic for the generic view.
- 🔄 **Data Source Implementation:** Adding robust fetching logic for FEC, Congress.gov, YouTube, etc. (`scripts/data-mining/sources/`).
- 🔄 **Data Processor Implementation:** Developing entity linking, advanced sentiment/topic analysis (`scripts/data-mining/processors/`).

### Planned
- 📋 Robust background task/queue system (beyond basic threading)
- 📋 Comprehensive Testing Framework (Unit, Integration)
- 📋 UI component development for entity relationship visualization
- 📋 Social media monitoring expansion (beyond single latest post)
- 📋 Campaign finance data integration & analysis features
- 📋 Reporting and dashboard features
- 📋 Deployment Strategy & CI/CD Pipeline

## Technical Debt & Considerations

1. **Database Schema Evolution**: As we continue to integrate more data sources, we need a systematic approach to schema migrations.

2. **API Rate Limiting**: Implementation of rate limiting and caching mechanisms for external APIs to prevent quota exhaustion.

3. **Testing Framework**: Need to establish comprehensive testing protocols, especially for the utility modules and data processors.

4. **Deployment Strategy**: Define the deployment process and environment requirements for production use.

## Next Steps (Immediate)

1. **Create Data Source Adapters**: Implement adapters for key data sources (Twitter, FEC, Congress.gov)

2. **Develop Entity Relationship Visualization**: Build UI components to visualize connections between political entities

3. **Implement Basic AI Analysis**: Integrate initial AI capabilities for summarizing political content

4. **Set Up Automated Data Collection**: Configure scheduled data collection jobs

## Dependencies & External Services

| Service | Purpose | Status |
|---------|---------|--------|
| Twitter API | Social media monitoring | API keys obtained |
| Google AI | Content analysis | Integrated |
| FEC API | Campaign finance data | Pending integration |
| Congress.gov | Legislative data | Initial integration |

## Known Issues

- SQLite performance limitations with large datasets remain a concern.
- Inconsistent field naming across some external data sources requires normalization.
- Twitter API v2 migration may be needed for expanded features.
- **Database interactions currently mocked in `coordinator.py`.**
- **Background task handling in `coordinator.py` is basic (`threading`).**

## Final Notes

The project has made significant strides in establishing the core data processing pipeline, integrating AI analysis, and structuring the backend scripts. Current focus is on fully integrating the database with the coordinator and completing the frontend implementation for the generic entity view. Subsequent work will involve fleshing out data sources and processors.

For detailed setup instructions, refer to the [README.md](./README.md) file.

## Recent Major Refactoring: Generic Entity Detail View

To improve code maintainability and scalability, we have refactored the way entity details are displayed:

1.  **Deprecated Separate Views:** The previous approach used separate views/logic for displaying politician details (`politician-view.html`/`.js`) and influencer details (`influencer-search.html`/`.js` modal).
2.  **Introduced Generic View:** We created a new, unified view:
    *   `src/renderer/entity-detail.html`: A generic HTML template for displaying details of *any* entity type.
    *   `src/renderer/entity-detail.js`: Handles the logic for this page, fetching data, populating common UI elements, and conditionally displaying type-specific information and actions.
3.  **Updated Navigation:**
    *   Clicking on a politician in `politician-view.js` now navigates to `entity-detail.html?type=politician&id=...`.
    *   Clicking on an influencer in `influencer-search.js` now navigates to `entity-detail.html?type=influencer&id=...`.
4.  **Cleaned Up Old Code:** Removed the profile display logic, related functions (`showPoliticianProfileById`, `showInfluencerDetails`, `fetchLatestTweet`, `analyzeLatestTweetWithAI`, etc.), and associated HTML elements (modals, profile sections) from the old view files (`politician-view.js`, `influencer-search.js`, `politician-view.html`, `influencer-search.html`).

## Current Backend Architecture & Data Flow

The primary flow for fetching/processing data involving Python scripts is now:

1.  **Frontend Request (`entity-detail.js`, etc.):** JavaScript prepares a JSON payload describing the desired action (e.g., `{type: 'evaluate_latest_post', entity_type: 'politician', ...}`).
2.  **IPC Call:** The payload is stringified and sent to the Electron main process via `window.electronAPI.invoke('python-bridge', jsonString)`. (The channel name 'python-bridge' needs to be confirmed/updated in `main.js` and `preload.js` if it differs).
3.  **Main Process (`main.js`):** Listens for `python-bridge` IPC events. Spawns the `api_bridge.py` script using Node.js `child_process`, passing the received JSON string as a command-line argument.
4.  **API Bridge Script (`scripts/api_bridge.py`):**
    *   Acts as a simple, secure pass-through.
    *   Takes the JSON string argument.
    *   Executes `scripts/data-mining/coordinator.py` using `subprocess.run`, passing the JSON string as an argument.
    *   Captures `stdout` and `stderr` from the coordinator.
    *   Validates the coordinator's `stdout` is valid JSON.
    *   Prints the coordinator's JSON response (or an error JSON) to its own `stdout`, which is read by the Electron main process.
5.  **Data Mining Coordinator (`scripts/data-mining/coordinator.py`):**
    *   The central Python logic hub.
    *   Parses the incoming JSON request from `api_bridge.py`.
    *   Routes the request based on the `type` field (e.g., `fetch`, `evaluate_latest_post`).
    *   Calls appropriate functions in `scripts/data-mining/sources/` (e.g., `twitter_profile.py`) or `scripts/data-mining/processors/` (e.g., `post_evaluator.py`).
    *   *Currently uses DummyDB for database interactions.* Needs integration with a real DB module.
    *   Handles background task queuing via `threading` for *some* flows (specifically *disabled* for `'evaluate_latest_post'` currently to minimize API calls).
    *   Formats the final result (data or error) as a JSON string and prints it to `stdout`.
6.  **Response Propagation:** The JSON response travels back: Coordinator -> API Bridge -> Main Process -> Renderer JS.
7.  **Frontend Update (`entity-detail.js`, etc.):** Parses the received JSON response and updates the UI accordingly.

## Implemented Features (Current Focus)

*   **Generic Detail View:** Basic HTML structure (`entity-detail.html`) and JS framework (`entity-detail.js`) are in place.
*   **Twitter Fetching:** `scripts/data-mining/sources/twitter_profile.py` implemented to fetch the latest tweet for a handle using `tweepy` and Bearer Token auth.
*   **AI Post Evaluation:** `scripts/data-mining/processors/post_evaluator.py` implemented to:
    *   Take tweet text.
    *   Use Google AI (Gemini Pro via `google-generativeai`) with a specific prompt.
    *   Analyze sentiment, identify topics, and suggest relevant *local* data types from a predefined list.
    *   Return results in a structured JSON format.
*   **Coordinator Logic:** `scripts/data-mining/coordinator.py` handles the `'evaluate_latest_post'` request type, orchestrating the call to `twitter_profile.fetch_latest_tweet` followed by `post_evaluator.evaluate_post_with_ai`. It explicitly *does not* queue background tasks for this flow.
*   **API Bridge:** `scripts/api_bridge.py` refactored to correctly call the coordinator.

## Configuration

*   A `.env` file is required in the project root (`MAGA_Ops/.env`).
*   It must contain:
    *   `GOOGLE_API_KEY="YOUR_GOOGLE_AI_API_KEY"`
    *   `TWITTER_BEARER_TOKEN="YOUR_TWITTER_BEARER_TOKEN"`
*   Ensure `python-dotenv` package is installed (`pip install python-dotenv`).
*   Ensure relevant API packages are installed (`pip install google-generativeai tweepy`).

## Immediate Next Steps (Frontend - `entity-detail.js`)

The core backend flow for tweet evaluation is set up, but the frontend needs work:

1.  **Implement `fetchAndDisplayEntityData`:** Currently calls coordinator for `base_profile`. Need to define what `base_profile` entails in the backend/DB and ensure this function correctly populates the common UI elements (`populateCommonUI`) and triggers type-specific setup (`setupEntityTypeSpecificUI`).
2.  **Implement `setupEntityTypeSpecificUI`:** Flesh out the logic to dynamically add tabs, fetch *additional* type-specific data (e.g., voting records, influencer metrics - currently uses dummy `populateList`), and display it correctly.
3.  **Refine `displayEvaluationResults`:** Ensure the UI within `#tweet-analysis-section` clearly presents the sentiment, topics, and suggested local data types returned by the AI evaluation.
4.  **Fix Back Button:** Implement robust back navigation in `setupEventListeners` (e.g., using `history.back()` or passing the previous URL).
5.  **Test Thoroughly:** Verify data fetching, display, and AI evaluation flow for both Politicians and Influencers via the new `entity-detail.html` page.

## Longer-Term / Backend Next Steps

*   **Database Implementation:** Replace `DummyDB` in `coordinator.py` with a real database module (e.g., `scripts/db/database_manager.py`) that interacts with the SQLite DB(s).
*   **Implement Data Sources:** Add real fetching logic to `youtube_channel.py`, `fec_lookup.py`, etc.
*   **Implement Processors:** Add logic to `entity_linker.py`, `sentiment_basic.py` (if different from `post_evaluator`).
*   **Background Task Robustness:** Replace simple `threading` in `coordinator.py` with a more robust queue system (e.g., Celery, RQ, or a persistent script) if background processing needs to survive script restarts.
*   **Schema Management:** Define a strategy for handling potential schema changes suggested by background tasks.
*   **API Usage Monitoring/Limits:** Implement stricter checks or configuration for API call frequency.

## Module Deep Dive: post_evaluator.py

**Path:** `scripts/data-mining/processors/post_evaluator.py`

### Technical Implementation Details

The `post_evaluator.py` module serves as an AI-powered text analysis service for political and social media content. It interfaces with Google's Generative AI (Gemini) to perform sentiment analysis, topic extraction, and contextual recommendations.

#### Core Functions

1. **evaluate_post_with_ai(post_text)**
   - **Purpose:** Analyzes a social media post or political statement using Google's Gemini API
   - **Input Validation:** Checks for empty input and API key availability
   - **API Interaction:** Constructs a detailed, structured prompt to the Gemini model requesting JSON output
   - **Response Processing:** Handles JSON extraction from model response (stripping code blocks)
   - **Error Handling:** Manages JSON parsing errors, API errors, and safety feedback
   - **Return Structure:** `{"success": bool, "data": {analysis_object} | None, "error": str | None, "raw_response": str | None}`

2. **generate_response(prompt)**
   - **Purpose:** Creates AI-generated text responses based on a provided prompt
   - **Input Validation:** Similar to evaluate_post_with_ai
   - **Safety Handling:** Detects and reports content moderation blocks
   - **Return Structure:** `{"success": bool, "data": {"generated_text": str} | None, "error": str | None}`

#### Technical Dependencies

- **google.generativeai**: Primary interface to Google's Gemini API
- **dotenv**: Environment variable management for API keys
- **json**: Used for structured data parsing/serialization
- **sys & os**: Path handling for correct .env file location
- **logging**: Structured diagnostic output

#### Authentication & Configuration

- **API Key Retrieval:** The module accesses the API key from environment variables:
  ```python
  API_KEY = os.getenv("GOOGLE_API_KEY")
  ```
- **Model Selection:** Uses the model `gemini-1.5-flash-latest` for optimal performance:
  ```python
  model = genai.GenerativeModel('gemini-1.5-flash-latest')
  ```
- **Environment Resolution:** Uses a three-level path traversal to locate the root `.env` file:
  ```python
  PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
  ```

#### Error Handling Architecture

The module implements sophisticated error handling:

1. **API Configuration Errors:** Detected during model initialization
2. **Empty Input Detection:** Both functions validate input before API calls
3. **JSON Parsing Errors:** Special handling for non-JSON responses from Gemini
4. **Content Safety Filters:** Detection of content policy violations with detailed reporting:
   ```python
   if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
       safety_info = response.prompt_feedback
       block_reason = safety_info.block_reason.name
   ```
5. **General Exception Handling:** Broad catch-all with context preservation

#### Prompt Engineering Details

The `evaluate_post_with_ai` function uses a specialized prompt template:

```
Analyze the following text post from a political figure or influencer. Provide the analysis as a JSON object with the following keys:
- "sentiment_classification": Classify the primary sentiment (e.g., Positive, Negative, Neutral, Mixed, Assertive, Critical, Supportive).
- "sentiment_justification": Briefly explain the reasoning for the sentiment classification (1-2 sentences).
- "main_topics": A list of 2-4 main political or social topics discussed or implied.
- "suggested_local_data": A list of 1-3 types of local data points or context that would be relevant for formulating a response or understanding the post's impact.

Text Post:
{post_text}

Provide the output strictly in JSON format:
```

This prompt engineering ensures:
- Structured output via explicit JSON formatting instructions
- Consistent sentiment classification with justification
- Topic extraction with controlled cardinality (2-4 topics)
- Generation of contextually relevant data suggestions

### Integration Points

1. **Coordinator Interface:** Primarily called from `scripts/data-mining/coordinator.py` as part of the `evaluate_latest_post` workflow
2. **Response Structure Compatibility:** Returns standardized success/error objects for consistent handling
3. **Error Propagation:** Detailed error data flows through coordinator → api_bridge → frontend
4. **Standalone Testing:** Includes self-contained test code when run directly:
   ```python
   if __name__ == '__main__':
       # Testing code with sample post
   ```

### Runtime Characteristics

- **Performance Considerations:**
  - Synchronous API calls (blocking execution)
  - Typical response time: 1-3 seconds per call
  - Memory usage: Minimal (~10-20MB)
  
- **Output Size Characteristics:**
  - JSON response typically 300-800 bytes
  - Key sentiments returned: Positive, Negative, Neutral, Mixed, Assertive, Critical, Supportive
  - Topics generally aligned with US political discourse domains

### Known Limitations & Future Enhancements

1. **API Rate Limiting:** No internal rate limiting implemented; relies on coordinator
2. **Caching:** No response caching for repeated analysis of identical content
3. **Model Versioning:** Hardcoded to `gemini-1.5-flash-latest` without fallback options
4. **Authentication Resilience:** Limited retry logic for transient auth failures
5. **Potential Enhancements:**
   - Add response caching with TTL
   - Implement alternative model fallbacks
   - Add explicit political bias detection
   - Improve streaming response support

### Usage Examples

When called through the coordinator (typical use case):
```json
{
  "type": "evaluate_latest_post",
  "entity_type": "politician",
  "entity_id": "P123"
}
```

Expected response structure (with sample data):
```json
{
  "success": true,
  "data": {
    "sentiment_classification": "Assertive",
    "sentiment_justification": "The post makes strong declarations about policy without equivocation.",
    "main_topics": ["Border Security", "Immigration", "National Security"],
    "suggested_local_data": ["Local Immigration Statistics", "Constituent Opinions on Border Security"]
  }
}
```

On API key configuration error:
```json
{
  "success": false,
  "error": "GOOGLE_API_KEY not configured properly."
}
``` 