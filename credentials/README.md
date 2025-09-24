# Credentials Directory

This directory contains sensitive Google Cloud service account credentials.

## Files that should be placed here:
- `google-credentials.json` - Your Google Cloud service account key

## Important Security Notes:
1. Never commit credential files to Git
2. Keep these files secure and private
3. Add this directory to .gitignore
4. Rotate credentials regularly

## Setup Instructions:
1. Follow the Google Cloud setup guide in GOOGLE_CLOUD_SETUP.md
2. Download your service account JSON key
3. Place it here as `google-credentials.json`
4. Update the path in `configs/google_ai_config.json`

## Alternative: Environment Variable
Instead of using a file, you can set:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
```