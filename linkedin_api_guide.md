# How to Get Your LinkedIn API Credentials

Getting LinkedIn API credentials is a multi-step process that requires creating a developer application and getting the right permissions.

### Step 1: Create a LinkedIn Developer Application

1.  **Go to the LinkedIn Developer Portal:**
    Navigate to [**developer.linkedin.com**](https://developer.linkedin.com/) and sign in with your LinkedIn account.

2.  **Create an App:**
    Click the "Create app" button. Fill in the required details, such as the app name and your company page (if applicable).

3.  **Request Product Access:**
    Once your app is created, go to the "Products" tab. You will need to request access to the following products:
    *   `Share on LinkedIn` (for posting to a personal profile)
    *   `Sign In with LinkedIn` (to get your user info)
    *   `Marketing Developer Platform` (often required for company page posting)

    For detailed instructions, follow the official guide: [**Getting Access to LinkedIn's Marketing APIs**](https://learn.microsoft.com/en-us/linkedin/marketing/getting-started?view=li-lms-2024-08).

### Step 2: Get an Access Token

1.  **Configure OAuth 2.0:**
    In your app settings, go to the "Auth" tab and configure your OAuth 2.0 redirect URLs (e.g., `https://www.google.com` can work for simple testing).

2.  **Generate an Access Token:**
    You need to complete the 3-legged OAuth 2.0 flow to generate an access token. This process involves authorizing your app to access your LinkedIn account.
    *   **Required Scopes:** When generating your token, you must request the following scopes:
        *   `r_liteprofile` (to get your Person ID)
        *   `w_member_social` (to post on your own behalf)
        *   `w_organization_social` (to post on behalf of a company)
    *   For a step-by-step guide on this flow, refer to the official documentation: [**LinkedIn's 3-Legged OAuth Flow**](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow?view=li-lms-2024-08).

### Step 3: Find Your Person ID and Organization ID

1.  **Person ID:**
    After getting your access token, you can find your Person ID by making an API call to the `/me` endpoint.
    *   **API Endpoint:** `https://api.linkedin.com/v2/me`
    *   The response will contain an `id` field (e.g., `uVzUQ8CUU9`). This is your Person ID.
    *   See the guide here: [**Retrieving Member Profiles**](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api?view=li-lms-2024-08).

2.  **Organization ID:**
    Your Organization ID is the numerical ID of your LinkedIn Company Page. You can usually find this in the URL of your company page's admin view. It is a sequence of numbers (e.g., `104469861`).