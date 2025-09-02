# Daily Knowledge Bot with AI Image Generation

This script automates the process of generating and posting daily content to LinkedIn. It fetches an interesting fact on a rotating topic, generates a professional LinkedIn post, creates a relevant AI-generated image, and can post the content to a personal or company LinkedIn page.

## Features

- **Daily Topics**: Automatically cycles through a list of topics from `topics.txt`.
- **Fact Generation**: Uses the Perplexity API to find a relevant article and summarize it into an interesting fact.
- **LinkedIn Post Crafting**: Generates a professional, engaging LinkedIn post based on the fact.
- **AI Image Generation**: Uses Google Cloud Vertex AI to create a unique, abstract image for each topic.
- **Content Archiving**: Saves all generated facts, posts, and images into organized local directories (`facts/`, `linkedin_posts/`, `images/`).
- **Interactive Posting**: Includes a manual confirmation step before publishing any content to LinkedIn.

## Prerequisites

1.  **Python 3.8+**
2.  **Google Cloud SDK**: You must have the `gcloud` command-line tool installed and authenticated. You can install it from [here](https://cloud.google.com/sdk/docs/install).

## Setup Instructions

### 1. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file `.env.example` to a new file named `.env`:

```bash
cp .env.example .env
```

Now, open the `.env` file and fill in your credentials. For detailed instructions on acquiring API keys and setting up each service, please refer to our setup guides:

- **[Google Cloud Setup Guide](./google_cloud_setup_guide.md)**
- **[Perplexity API Setup Guide](./perplexity_api_guide.md)**
- **[LinkedIn API Setup Guide](./linkedin_api_guide.md)**

A summary of the required keys is provided below.

#### Perplexity API Key

- Go to your [Perplexity AI API Settings](https://www.perplexity.ai/settings/api) to generate an API key.
- Add it to your `.env` file:
  ```
  PERPLEXITY_API_KEY="YOUR_PERPLEXITY_API_KEY_HERE"
  ```

#### Google Cloud Credentials

- **Project ID**: Create or select a project in the [Google Cloud Console](https://console.cloud.google.com/). Your Project ID is listed on the dashboard.
- **Enable APIs**: In your Google Cloud project, you must enable the **Vertex AI API**. You can use [this link](https://console.developers.google.com/apis/api/aiplatform.googleapis.com/overview) to enable it for your selected project.
- **Enable Billing**: The Vertex AI API requires a project linked to an active billing account. You can enable billing from your project's [Billing page](https://console.cloud.google.com/billing).
- Add your Project ID to the `.env` file:
  ```
  GOOGLE_PROJECT_ID="YOUR_GOOGLE_PROJECT_ID_HERE"
  ```

#### LinkedIn API Credentials

- You need a LinkedIn application with the `r_liteprofile`, `w_member_social`, and (for company pages) `w_organization_social` permissions.
- **Access Token**: Generate an access token for your application with the required scopes.
- **Person ID**: This is your unique LinkedIn user ID. You can find it by inspecting the API response after authenticating or from your profile URL.
- **Organization ID**: If posting to a company page, this is the ID of your LinkedIn organization.
- Add your LinkedIn credentials to the `.env` file.

### 3. Authenticate with Google Cloud

Before running the script for the first time, you must authenticate your local machine with Google Cloud. Run the following command in your terminal and follow the browser-based login process:

```bash
gcloud auth application-default login
```

## Usage

### Generate Content without Posting

To run the script, fetch the daily content, and save all artifacts locally without posting to LinkedIn:

```bash
python daily_knowledge_bot.py
```

### Post to Your Personal LinkedIn Profile

To generate content and post it to the personal profile specified by `LINKEDIN_PERSON_ID`:

```bash
python daily_knowledge_bot.py --post-to-linkedin
```
The script will display the post and image and ask for your confirmation before publishing.

### Post to a LinkedIn Company Page

To generate content and post it to the company page specified by `LINKEDIN_ORGANIZATION_ID`:

```bash
python daily_knowledge_bot.py --post-to-linkedin --company
```
**Note**: This requires your LinkedIn application to have the `w_organization_social` permission scope, which requires approval from LinkedIn.

## Customization

You can customize the daily topics by editing the `topics.txt` file. Add one topic per line. The script will cycle through these topics day by day.
