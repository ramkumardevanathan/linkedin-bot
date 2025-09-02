# Google Cloud Setup Guide for AI Image Generation

This guide provides detailed steps to configure your Google Cloud account to use the Vertex AI API for image generation. Follow these instructions to get your Project ID and set up the necessary permissions and authentication.

---

### Step 1: Create a Google Cloud Account and Project

First, you need a Google Cloud account and a project to house your resources.

1.  **Sign Up for Google Cloud**: If you don't already have an account, sign up at the [Google Cloud Console](https://console.cloud.google.com/). New users are often eligible for a free trial with credits, which is more than enough for this project.

2.  **Create a New Project**:
    *   Once logged in, go to the [Project Selector](https://console.cloud.google.com/projectselector2/home/dashboard) page.
    *   Click **"Create Project"**.
    *   Give your project a memorable name (e.g., "AI-Knowledge-Bot").
    *   After the project is created, make sure it is selected in the top navigation bar.

3.  **Find Your Project ID**: The **Project ID** is a unique identifier for your project. You will need this for your `.env` file. You can find it on the main [Dashboard](https://console.cloud.google.com/home/dashboard) of your project.

---

### Step 2: Enable Billing for Your Project

Google Cloud's advanced AI services, including Vertex AI, require a project to be linked to a billing account.

1.  **Go to the Billing Page**: Navigate to your project's [Billing section](https://console.cloud.google.com/billing).

2.  **Link a Billing Account**: If your project doesn't have a billing account, you will be prompted to **"Link a billing account"** or **"Create billing account"**. Follow the on-screen instructions.

    *Note: While a billing account is required, usage for this script is likely to fall within the free tier provided by Google Cloud, making it free or very low-cost to run.*

---

### Step 3: Enable the Vertex AI API

Before you can use the Vertex AI service, you must enable its API for your project.

1.  **Navigate to the API Library**: Go to the [Vertex AI API page](https://console.developers.google.com/apis/api/aiplatform.googleapis.com/overview) in the API Library.

2.  **Enable the API**: Ensure your correct project is selected in the top navigation bar, and then click the **"Enable"** button. It may take a few minutes for the API to become fully active.

---

### Step 4: Install and Authenticate the Google Cloud SDK

To allow the script to securely access your Google Cloud account from your local machine, you need to install the `gcloud` command-line tool and authenticate.

1.  **Install the Google Cloud SDK**: Follow the official instructions to install the SDK for your operating system:
    *   [Google Cloud SDK Installation Guide](https://cloud.google.com/sdk/docs/install)

2.  **Authenticate Your Local Environment**: After installation, run the following command in your terminal. This will open a browser window for you to log in to your Google account and grant the SDK permission to access your cloud resources.

    ```bash
    gcloud auth application-default login
    ```

    This command sets up **Application Default Credentials (ADC)**, which is a secure way for local applications to authenticate with Google Cloud services without needing to handle secret keys in your code.

---

**Setup is now complete!** With your Project ID in the `.env` file and your local authentication configured, the script will have everything it needs to generate images using Vertex AI.
