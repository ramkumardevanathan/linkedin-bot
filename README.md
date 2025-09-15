# Daily Knowledge Bot

A Python application that delivers interesting facts about rotating topics using the Perplexity AI API. Perfect for daily learning, newsletter content, or personal education.

## 🌟 Features

- **Daily Topic Rotation**: Automatically selects topics based on the day of the month.
- **AI-Powered Content**: Uses the Perplexity API to find relevant articles and generate engaging LinkedIn posts.
- **Optional AI-Generated Images**: Uses Google's Gemini API to create high-quality, relevant images (disabled by default).
- **LinkedIn Integration**: Post directly to personal profiles or company pages.
- **Professional Formatting**: Clean, mobile-friendly posts with emoji-based lists and proper hashtag placement.
- **Customizable Logo Watermarking**: Option to add your brand's logo to generated images.
- **Configurable & Extensible**: Customize topics, manage API keys, and extend functionality.

## 📋 Requirements

- Python 3.7+
- Google API key with access to Gemini API
- Required packages:
  - `requests`
  - `python-dotenv`
  - `google-generativeai`
  - `Pillow`

## 🔧 Usage

### Basic Commands

- **Generate content locally (saves to files but doesn't post):**
  ```bash
  python daily_knowledge_bot.py
  ```

- **Generate and post to your personal LinkedIn profile:**
  ```bash
  python daily_knowledge_bot.py --post-to-linkedin
  ```

- **Generate and post to a LinkedIn Company Page (requires permissions):**
  ```bash
  python daily_knowledge_bot.py --post-to-linkedin --company
  ```

### Advanced Options

- **Enable image generation (disabled by default):**
  ```bash
  python daily_knowledge_bot.py --add-image
  ```

- **Skip adding logo to images (only applicable with --add-image):**
  ```bash
  python daily_knowledge_bot.py --add-image --no-logo
  ```

- **Post to LinkedIn with an image:**
  ```bash
  python daily_knowledge_bot.py --post-to-linkedin --add-image
  ```

- **Post to company page with a custom image (no logo):**
  ```bash
  python daily_knowledge_bot.py --post-to-linkedin --company --add-image --no-logo
  ```

## 🚀 Installation

1. Clone this repository or download the script
2. Install the required packages:

```bash
# Install from requirements file (recommended)
pip install -r requirements.txt

# Or install manually
pip install requests python-dotenv google-generativeai Pillow
```

3. Create a `.env` file in the same directory as the script and add the following environment variables. See the `.env.example` file for a template.

   ```
   # Perplexity API Key
   PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY_HERE"

   # Google Gemini API Configuration
   GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"

   # LinkedIn API Credentials (required for posting)
   LINKEDIN_ACCESS_TOKEN="YOUR_LINKEDIN_ACCESS_TOKEN_HERE"
   LINKEDIN_PERSON_ID="YOUR_LINKEDIN_PERSON_ID_HERE"
   LINKEDIN_ORGANIZATION_ID="YOUR_LINKEDIN_ORGANIZATION_ID_HERE" # Optional, for company pages
   ```

4. **Get a Google API Key**:
   - Go to [Google AI Studio](https://makersuite.google.com/)
   - Sign in with your Google account
   - Go to the API Keys section
   - Create a new API key
   - Copy the key and add it to your `.env` file as `GOOGLE_API_KEY`

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

### Required Environment Variables (in `.env` file):

- `PERPLEXITY_API_KEY`: Your Perplexity API key for content generation
- `GOOGLE_API_KEY`: Required if using image generation (--add-image)
- `LINKEDIN_ACCESS_TOKEN`: Required for LinkedIn posting
- `LINKEDIN_PERSON_ID`: Your LinkedIn person ID (for personal posts)
- `LINKEDIN_ORGANIZATION_ID`: Your company's LinkedIn ID (for company posts)

### Optional Environment Variables:
- `OUTPUT_DIR`: Directory to save generated content (default: current directory)
- `TOPICS_FILE`: Path to custom topics file (default: topics.txt in script directory)

## 🖼️ Image Generation

By default, the bot runs without generating images. To include AI-generated images in your posts:

1. Set up your `GOOGLE_API_KEY` in the `.env` file
2. Add the `--add-image` flag when running the script
3. Optionally, place a `brand_logo.png` in the script directory for watermarking

Example with image generation:
```bash
python daily_knowledge_bot.py --post-to-linkedin --add-image
```

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
