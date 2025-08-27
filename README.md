# Daily Knowledge Bot for LinkedIn

This Python script automates the process of generating and posting daily facts on rotating topics to a LinkedIn personal profile or a company page. It uses the Perplexity API to find and summarize a verifiable online article, ensuring every post is backed by a source.

## Features

- **Automated Content Creation:** Fetches and summarizes a new article each day based on a list of topics.
- **LinkedIn Integration:** Posts generated content directly to LinkedIn.
- **Flexible Posting:** Supports posting to a personal profile or a LinkedIn Company Page.
- **Interactive Review:** Displays the generated post for manual review and confirmation before publishing.
- **Secure Configuration:** Keeps all API keys and sensitive information safe in a [.env](cci:7://file:///Users/ramkumar.devanathan/Downloads/api-cookbook-main/docs/examples/daily-knowledge-bot/.env:0:0-0:0) file.
- **Robust & Reliable:** Uses a two-step process to first find a source URL and then summarize it, guaranteeing a sourced fact every time.

## Setup Instructions

### 1. Prerequisites

- Python 3.7+
- A Perplexity AI API Key
- A LinkedIn account with a registered application to get API credentials.

### 2. Installation

1.  **Create a Project Directory:**
    Create a folder for the project and navigate into it.

2.  **Set up a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *(On Windows, use `venv\Scripts\activate`)*

3.  **Install Dependencies:**
    Install the required Python packages using the provided `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

1.  **Create a `.env` file:**
    This project uses a `.env` file to manage secret keys. Copy the example file to create your own configuration file:
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:**
    Open the `.env` file in a text editor and fill in your credentials.
    - `PERPLEXITY_API_KEY`: Your API key from Perplexity AI.
    - `LINKEDIN_ACCESS_TOKEN`: Your LinkedIn API access token.
    - `LINKEDIN_PERSON_ID`: Your LinkedIn person URN (e.g., `abCDef123`).
    - `LINKEDIN_ORGANIZATION_ID`: The ID of the LinkedIn Company Page you want to post to (e.g., `12345678`). This is only required if you plan to post on behalf of an organization.

**NOTE** - refer to the `perplexity_api_guide.md` and `linkedin_api_guide.md` files for more details on how to obtain the api keys.

### 4. Customize Topics

Open the `topics.txt` file and add or remove topics as you see fit. The script will cycle through these topics day by day.

## Usage

You can run the script from your terminal with different flags to control its behavior.

### To Generate a Fact (without posting)

This is useful for testing. It will create a fact file in the `facts/` directory.

```bash
python3 daily_knowledge_bot_final.py
```

### To Post to Your Personal LinkedIn Profile

This will generate the content, show you a preview, and ask for confirmation before posting to your personal profile.

```bash
python3 daily_knowledge_bot_final.py --post-to-linkedin
```

### To Post to a LinkedIn Company Page

This will generate the content, show you a preview, and ask for confirmation before posting to the company page specified in your `.env` file.

```bash
python3 daily_knowledge_bot_final.py --post-to-linkedin --company
```
