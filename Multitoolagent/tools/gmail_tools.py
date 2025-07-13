import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.adk.tools import FunctionTool

# If modifying these scopes, delete the file /Users/mrunmayeerane/Desktop/hackathon/weavehacks_dynamove/Multitoolagent/tools/token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_latest_emails():
    """
    Get the user's latest emails from Gmail.
    
    Returns:
        String with formatted email information
    """
    creds = None
    # The file /Users/mrunmayeerane/Desktop/hackathon/weavehacks_dynamove/Multitoolagent/tools/token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("/Users/mrunmayeerane/Desktop/hackathon/weavehacks_dynamove/Multitoolagent/tools/token.json"):
        creds = Credentials.from_authorized_user_file("/Users/mrunmayeerane/Desktop/hackathon/weavehacks_dynamove/Multitoolagent/tools/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "/Users/mrunmayeerane/Desktop/hackathon/weavehacks_dynamove/Multitoolagent/tools/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("/Users/mrunmayeerane/Desktop/hackathon/weavehacks_dynamove/Multitoolagent/tools/token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)

        # List the 10 most recent messages
        results = service.users().messages().list(userId="me", labelIds=['INBOX'], maxResults=10).execute()
        messages = results.get("messages", [])

        if not messages:
            return "No messages found in inbox."
        
        email_summaries = []
        email_summaries.append(f"📧 **Latest {len(messages)} emails:**\n")

        for i, message in enumerate(messages):
            msg = service.users().messages().get(userId="me", id=message["id"]).execute()
            
            # Get the From and Subject headers
            headers = msg['payload']['headers']
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
            from_sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
            date = next((header['value'] for header in headers if header['name'] == 'Date'), 'Unknown Date')

            # Get the message body
            body_text = "No body content available"
            if 'parts' in msg['payload']:
                parts = msg['payload']['parts']
                if parts and 'body' in parts[0] and 'data' in parts[0]['body']:
                    data = parts[0]['body']['data']
                    data = data.replace("-","+").replace("_","/")
                    decoded_data = base64.b64decode(data)
                    body_text = decoded_data.decode('utf-8').strip()
            elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                data = msg['payload']['body']['data']
                data = data.replace("-","+").replace("_","/")
                decoded_data = base64.b64decode(data)
                body_text = decoded_data.decode('utf-8').strip()
            
            # Truncate body if too long
            if len(body_text) > 300:
                body_text = body_text[:300] + "..."

            email_summaries.append(f"**{i}. {subject}**")
            email_summaries.append(f"   �� From: {from_sender}")
            email_summaries.append(f"   📅 Date: {date}")
            email_summaries.append(f"   📝 Body: {body_text}")
            email_summaries.append("")

        return "\n".join(email_summaries)

    except HttpError as error:
        return f"❌ Gmail API error: {error}"
    except Exception as error:
        return f"❌ Unexpected error: {error}"
    
GmailLatestEmailsTool = FunctionTool(get_latest_emails)

if __name__ == "__main__":
    print(get_latest_emails())