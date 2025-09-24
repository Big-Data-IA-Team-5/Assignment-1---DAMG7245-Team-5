# Google Cloud Document AI Setup Guide
Team 5 - DAMG7245 Fall 2025

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your **Project ID** (e.g., `my-doc-ai-project-123456`)

## Step 2: Enable Document AI API

1. In Google Cloud Console, go to **APIs & Services > Library**
2. Search for "Document AI API"
3. Click **Enable**

## Step 3: Create Document AI Processor

1. Go to **Document AI > Processors**
2. Click **Create Processor**
3. Choose **Document OCR** (for general text extraction)
4. Select region: **us** (or your preferred region)
5. Note the **Processor ID** (long string like `abc123def456...`)

## Step 4: Create Service Account

1. Go to **IAM & Admin > Service Accounts**
2. Click **Create Service Account**
3. Name: `document-ai-service`
4. Description: `Service account for Document AI integration`
5. Click **Create and Continue**

## Step 5: Add Roles

Add these roles to your service account:
- **Document AI API User**
- **Storage Object Viewer** (if using Cloud Storage)

## Step 6: Create and Download Key

1. Click on your service account
2. Go to **Keys** tab
3. Click **Add Key > Create New Key**
4. Choose **JSON** format
5. Download the JSON file
6. **IMPORTANT**: Save it securely as `google-credentials.json`

## Step 7: Update Configuration

1. Edit `configs/google_ai_config.json`:

```json
{
  "google_document_ai": {
    "project_id": "YOUR-ACTUAL-PROJECT-ID",
    "location": "us",
    "processor_id": "YOUR-ACTUAL-PROCESSOR-ID",
    "credentials_path": "credentials/google-credentials.json"
  },
  "output_settings": {
    "save_temp_pdfs": true,
    "save_json_results": true,
    "save_parsed_results": true,
    "generate_comparison": true
  },
  "page_selection": {
    "default_pages": [5, 12],
    "random_seed": 42,
    "max_random_pages": 5
  }
}
```

## Step 8: Set Up Credentials

Create a `credentials/` folder and place your JSON file there:

```bash
mkdir -p credentials
# Move your downloaded JSON file to credentials/google-credentials.json
mv ~/Downloads/your-service-account-key.json credentials/google-credentials.json
```

## Step 9: Set Environment Variable (Alternative)

Instead of using a file path, you can set an environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="credentials/google-credentials.json"
```

## Step 10: Test the Setup

Run the Lab 7 demo:

```bash
# Extract pages 5 and 12 from Tesla PDF and send to Google AI
python src/google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12

# Extract 2 random pages
python src/google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2 --seed 42
```

## Expected Output Structure

```
reports/google_ai/lab7_session_20250923_143022/
├── temp_pdfs/                  # Extracted page PDFs
│   └── tesla_pages_5_12.pdf
├── raw_google_ai_results/      # Raw API responses
│   └── tesla_pages_5_12_google_ai.json
├── parsed_results/             # Structured data
│   ├── text_extraction.json
│   ├── table_extraction.csv
│   └── entity_extraction.json
├── lantern_comparison/         # Comparison analysis
│   └── google_ai_vs_lantern.json
└── final_reports/              # Comprehensive reports
    └── lab7_analysis_report.md
```

## Troubleshooting

### Error: "DefaultCredentialsError"
- Ensure your JSON file path is correct in the config
- Try setting `GOOGLE_APPLICATION_CREDENTIALS` environment variable

### Error: "PermissionDenied"
- Check that Document AI API is enabled
- Verify service account has correct roles

### Error: "ProcessorNotFound"
- Verify your processor ID is correct
- Ensure the processor exists in the specified location

### Error: "QuotaExceeded"
- Document AI has usage limits
- Check your project quotas in Google Cloud Console

## Security Notes

1. **Never commit credentials to Git**
2. Add `credentials/` to your `.gitignore`
3. Keep your service account JSON file secure
4. Regularly rotate your service account keys

## Cost Information

- Document AI pricing: https://cloud.google.com/document-ai/pricing
- First 1,000 pages per month are free
- Additional pages: $0.015 per page for Document OCR

---

## Quick Start Commands

After setup is complete:

```bash
# Test with specific pages
python src/google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 1 5 10

# Test with random pages
python src/google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 3 --seed 42

# Use custom config
python src/google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12 --config configs/my_config.json
```