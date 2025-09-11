

# Daily Knowledge Bot

A Python application that delivers interesting facts about rotating topics using the Perplexity AI API. Perfect for daily learning, newsletter content, or personal education.

## 🌟 Features

- **Daily Topic Rotation**: Automatically selects topics based on the day of the month.
- **AI-Powered Content**: Uses the Perplexity API to find relevant articles and generate summaries.
- **AI-Generated Images**: Uses Google Vertex AI to create high-quality, relevant images for each topic.
- **LinkedIn Integration**: Can post the generated content directly to a personal or company LinkedIn page.
- **Customizable Logo Watermarking**: Automatically adds your brand's logo to every generated image.
- **Configurable & Extensible**: Easily customize topics, manage API keys, and add new functionality.

## 📋 Requirements

- Python 3.7+
- A Google Cloud project with the Vertex AI API enabled.
- Required packages:
  - `requests`
  - `python-dotenv`
  - `google-cloud-aiplatform`
  - `Pillow`

## 🚀 Installation

1. Clone this repository or download the script
2. Install the required packages:

```bash
# Install from requirements file (recommended)
pip install -r requirements.txt

# Or install manually
pip install requests python-dotenv google-cloud-aiplatform Pillow
```

3. Create a `.env` file in the same directory as the script and add the following environment variables. See the `.env.example` file for a template.

   ```
   # Perplexity API Key
   PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY_HERE"

   # Google Cloud Configuration
   GOOGLE_PROJECT_ID="YOUR_GOOGLE_CLOUD_PROJECT_ID"
   GOOGLE_LOCATION="us-central1" # Or your preferred region

   # LinkedIn API Credentials (required for posting)
   LINKEDIN_ACCESS_TOKEN="YOUR_LINKEDIN_ACCESS_TOKEN_HERE"
   LINKEDIN_PERSON_ID="YOUR_LINKEDIN_PERSON_ID_HERE"
   LINKEDIN_ORGANIZATION_ID="YOUR_LINKEDIN_ORGANIZATION_ID_HERE" # Optional, for company pages
   ```

4. **Add Your Brand Logo**:
   - Place your company's logo in the same directory as the script.
   - The logo file **must be named `brand_logo.png`**. A sample has been provided, but you should replace it with your own.

## 🔧 Usage

### Running the Bot

The script can be run with several command-line flags to control its behavior:

- **Generate content locally (default behavior)**:
  ```bash
  python daily_knowledge_bot.py
  ```

- **Generate content and post to LinkedIn**:
  ```bash
  python daily_knowledge_bot.py --post-to-linkedin
  ```

- **Post to a LinkedIn Company Page**:
  ```bash
  python daily_knowledge_bot.py --post-to-linkedin --company
  ```

- **Generate content without adding the logo**:
  ```bash
  python daily_knowledge_bot.py --no-logo
  ```

This will:
1. Select a topic based on the current day
2. Fetch an interesting fact from Perplexity AI
3. Save the fact to a dated text file in your current directory
4. Display the fact in the console

### Customizing Topics

Edit the `topics.txt` file (one topic per line) or modify the `topics` list directly in the script.

Example topics:
```
astronomy
history
biology
technology
psychology
ocean life
ancient civilizations
quantum physics
art history
culinary science
```

### Automated Scheduling

#### On Linux/macOS (using cron):

```bash
# Edit your crontab
crontab -e

# Add this line to run daily at 8:00 AM
0 8 * * * /path/to/python3 /path/to/daily_knowledge_bot.py
```

#### On Windows (using Task Scheduler):

1. Open Task Scheduler
2. Create a new Basic Task
3. Set it to run daily
4. Add the action: Start a program
5. Program/script: `C:\path\to\python.exe`
6. Arguments: `C:\path\to\daily_knowledge_bot.py`

## 🔍 Configuration Options

The following environment variables can be set in your `.env` file:

- `PERPLEXITY_API_KEY` (required): Your Perplexity API key
- `OUTPUT_DIR` (optional): Directory to save fact files (default: current directory)
- `TOPICS_FILE` (optional): Path to your custom topics file

## 📄 Output Example

```
DAILY FACT - 2025-04-02
Topic: astronomy

Saturn's iconic rings are relatively young, potentially forming only 100 million years ago. This means dinosaurs living on Earth likely never saw Saturn with its distinctive rings, as they may have formed long after the dinosaurs went extinct. The rings are made primarily of water ice particles ranging in size from tiny dust grains to boulder-sized chunks.
```

## 🛠️ Extending the Bot

Some ways to extend this bot:
- Add email or SMS delivery capabilities
- Create a web interface to view fact history
- Integrate with social media posting
- Add multimedia content based on the facts
- Implement advanced scheduling with specific topics on specific days

## ⚠️ Limitations

- API rate limits may apply based on your Perplexity account
- Quality of facts depends on the AI model
- The free version of the Sonar API has a token limit that may truncate longer responses

## 📜 License

[MIT License](https://github.com/ppl-ai/api-cookbook/blob/main/LICENSE)

## 🙏 Acknowledgements

- This project uses the Perplexity AI API (https://docs.perplexity.ai/)
- Inspired by daily knowledge calendars and fact-of-the-day services
