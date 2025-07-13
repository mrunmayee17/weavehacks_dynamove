# Gmail API Setup Guide

This guide will help you set up Gmail API access for the restaurant booking assistant.

## Prerequisites

- Google account with Gmail
- Python 3.7+
- Required Python packages (install with `pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client`)

## Step 1: Enable Gmail API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click on it and press "Enable"

## Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application" as the application type
4. Give it a name (e.g., "Restaurant Booking Assistant")
5. Click "Create"
6. Download the JSON file and rename it to `credentials.json`
7. Place `credentials.json` in the project root directory (same level as `Multitoolagent/`)

## Step 3: First Run Authentication

1. Run the Streamlit app: `streamlit run Multitoolagent/app.py`
2. The first time you use Gmail features, a browser window will open
3. Sign in with your Google account
4. Grant permission to access your Gmail
5. A `token.json` file will be created automatically

## Step 4: Test Gmail Integration

1. Run the test script: `python test_gmail_tools.py`
2. Try Gmail commands in the app:
   - "Show me my latest emails"
   - "Search for emails from john@example.com"
   - "Find emails about meetings"

## Gmail Search Queries

The Gmail search supports various query formats:

- `from:email@example.com` - Emails from specific sender
- `to:email@example.com` - Emails sent to specific address
- `subject:keyword` - Emails with keyword in subject
- `has:attachment` - Emails with attachments
- `is:important` - Important emails
- `label:work` - Emails with specific label
- `after:2024/01/01` - Emails after specific date
- `before:2024/12/31` - Emails before specific date

## Security Notes

- Keep `credentials.json` and `token.json` secure and don't commit them to version control
- The app only requests read-only access to Gmail
- You can revoke access anytime in your Google Account settings

## Troubleshooting

### "credentials.json not found"
- Make sure `credentials.json` is in the project root directory
- Check that the file name is exactly `credentials.json` (not `credentials.json.json`)

### "Invalid credentials" error
- Delete `token.json` and try again
- Make sure your Google account has Gmail enabled

### "Quota exceeded" error
- Gmail API has daily quotas
- Check your usage in Google Cloud Console
- Consider implementing rate limiting for production use

## Example Usage

Once set up, you can use voice or text commands like:

- "Show me my 5 latest emails"
- "Search for emails about restaurant reservations"
- "Find emails from my boss from last week"
- "Show me important emails with attachments"

The assistant will format the results nicely and provide email previews with sender, subject, date, and content snippets. 