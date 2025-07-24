from atproto import Client
from dotenv import load_dotenv
import os
import re # Import regex module

def clean_string(s):
    """Removes common non-printable ASCII characters from a string."""
    if s is None:
        return None
    # Use a raw string literal for the regex pattern to avoid issues with backslashes
    return re.sub(r'[^\x20-\x7E\n\r\t]', '', s)

load_dotenv()
username = clean_string(os.environ.get('BLUESKY_USERNAME'))
password = clean_string(os.environ.get('BLUESKY_PASSWORD'))

client = Client()
c = client.login(username,password)

