# PDF Analyzer with Gemini 3 Pro

A powerful Streamlit desktop application for batch analyzing PDF files using Google's Gemini AI API. Extract structured information from multiple PDFs and export results to Excel with ease.

## Features

- **Flexible PDF Input**: Upload individual files or scan entire folders recursively
- **Custom Analysis**: Define your own prompts and output columns
- **AI-Powered Extraction**: Leverages Gemini 3 Pro for intelligent document analysis
- **Batch Processing**: Analyze multiple PDFs with progress tracking and error handling
- **Excel Export**: Generates formatted spreadsheets with auto-sized columns
- **Template System**: Save and reuse prompt configurations
- **Robust Error Handling**: Automatic retries, rate limiting, and detailed status reporting

## Prerequisites

- Python 3.11 or higher
- A Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

## Installation

1. **Clone or download this repository**

```bash
cd llm-pdf-parse
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up your API key**

Create a `.env` file in the project root:

```bash
# On Windows
copy .env.example .env

# On macOS/Linux
cp .env.example .env
```

Edit the `.env` file and add your Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

Alternatively, set the environment variable directly:

```bash
# Windows (Command Prompt)
set GEMINI_API_KEY=your_actual_api_key_here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your_actual_api_key_here"

# macOS/Linux
export GEMINI_API_KEY=your_actual_api_key_here
```

## Usage

### Starting the Application

```bash
streamlit run app.py

# Or if 'streamlit' command is not found:
python -m streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

### Workflow

#### 1. Configure Your Analysis (Configure Tab)

**Define Output Columns:**
- The first column "Document Name" is automatically populated with PDF filenames
- Add custom columns for the data you want to extract (e.g., "Contract Type", "Effective Date", "Key Terms")
- Remove columns by clicking the trash icon

**Write Your Analysis Prompt:**
- Describe what you want Gemini to extract from each PDF
- Be specific about the type of information you're looking for
- Example:
  ```
  Analyze this legal contract and extract key information.
  Focus on:
  - Contract type and parties involved
  - Important dates (effective date, expiration, renewal dates)
  - Financial terms and payment obligations
  - Key clauses and special conditions
  ```

#### 2. Select PDF Files (Analyze Tab)

**Option A: Upload Files**
- Click "Browse files" and select one or more PDF files
- Supports multiple file selection

**Option B: Folder Path**
- Enter the full path to a folder containing PDFs
- Click "Scan Folder" to recursively find all PDF files
- Example paths:
  - Windows: `C:\Users\YourName\Documents\Contracts`
  - macOS/Linux: `/Users/yourname/Documents/contracts`

#### 3. Start Analysis

- Click "Start Analysis" to begin batch processing
- Monitor progress with the real-time progress bar
- View per-document status messages as they're processed

#### 4. Review and Export Results (Results Tab)

- View results in an interactive table
- Check processing status for each document
- Download results as an Excel file (.xlsx)
- Clear results to start a new analysis

### Template Management

**Save a Template:**
1. Configure your prompt and columns
2. Open the sidebar
3. Click "Save Current Configuration"
4. Download the JSON template file

**Load a Template:**
1. Open the sidebar
2. Click "Browse files" under "Load Template"
3. Select a previously saved template JSON file
4. Your prompt and columns will be automatically populated

## Configuration Options (Sidebar)

### Model Selection
- **gemini-3-pro-preview**: Most capable, recommended for complex analysis
- **gemini-2.5-flash**: Faster and more cost-effective for simpler tasks

### API Delay
- Delay in seconds between API requests
- Default: 1.0 second
- Increase if you encounter rate limiting errors

### Max Retries
- Number of retry attempts for failed requests
- Default: 2 retries
- Useful for handling temporary API issues

## Project Structure

```
llm-pdf-parse/
├── app.py              # Main Streamlit application
├── gemini_client.py    # Gemini API interaction logic
├── excel_export.py     # Excel file generation
├── prompt_builder.py   # Prompt construction logic
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment variables
└── README.md          # This file
```

## Module Documentation

### `gemini_client.py`
Handles all Gemini API interactions:
- PDF file upload to Gemini Files API
- Content generation with retry logic
- JSON response parsing
- Automatic cleanup of uploaded files

### `prompt_builder.py`
Constructs prompts for Gemini:
- Combines user prompt with structured JSON output instructions
- Ensures consistent response formatting
- Provides default prompt templates

### `excel_export.py`
Creates formatted Excel files:
- Writes headers with bold styling
- Auto-sizes columns based on content
- Handles multi-line text with word wrapping
- Exports results as binary Excel data

### `app.py`
Main Streamlit application:
- Three-tab interface (Configure, Analyze, Results)
- Session state management
- PDF file handling (upload and folder scanning)
- Progress tracking and status reporting
- Template save/load functionality

## Example Use Case

**Scenario:** Analyzing 50 legal contracts to extract key terms

1. **Configure:**
   - Add columns: "Contract Type", "Effective Date", "Parties", "Payment Terms", "Termination Clause"
   - Write prompt: "Extract key contractual information from this legal document..."

2. **Analyze:**
   - Select folder: `C:\Users\Blake\Documents\Contracts`
   - Click "Scan Folder" → finds 50 PDFs
   - Click "Start Analysis"

3. **Results:**
   - Review extracted data in the table
   - Download Excel file with 50 rows × 6 columns
   - Share spreadsheet with team

## Troubleshooting

### "GEMINI_API_KEY not set in environment"
- Ensure your `.env` file exists and contains the API key
- Or set the environment variable before running the app
- Restart the Streamlit app after setting the environment variable

### "Error uploading file" or API errors
- Check your API key is valid
- Verify you have available API quota
- Increase the API Delay setting in the sidebar
- Check your internet connection

### PDF files not found in folder
- Verify the folder path is correct
- Ensure the path uses the correct format for your OS (forward or backward slashes)
- Check that PDF files exist in the folder or subfolders
- Verify you have read permissions for the folder

### JSON parsing errors
- Gemini occasionally returns responses that aren't valid JSON
- The app will store the raw response in a "Raw Response" column
- Try adjusting your prompt to be more specific about the expected output
- Consider using gemini-3-pro-preview for better structured output

### Rate limiting errors
- Increase the "API Delay" setting in the sidebar
- Reduce batch size by processing fewer PDFs at once
- Check your API usage limits in Google AI Studio

## API Costs

Gemini API usage is billed based on:
- Input tokens (PDF content + prompt)
- Output tokens (generated response)

**Tips to reduce costs:**
- Use `gemini-2.5-flash` for simpler extraction tasks
- Keep prompts concise but specific
- Process smaller PDFs when possible
- Use templates to avoid rewriting prompts

Check current pricing at: https://ai.google.dev/pricing

## Security Notes

- **API Key Protection**: Never commit your `.env` file to version control
- **Local Processing**: PDFs are temporarily uploaded to Gemini's servers for analysis
- **Auto Cleanup**: The app automatically deletes uploaded files from Gemini after processing
- **Sensitive Documents**: Be mindful of your organization's data policies when uploading confidential documents

## Limitations

- Maximum PDF size: Limited by Gemini API constraints (typically 20-30 MB)
- Processing speed: Depends on API rate limits and file size
- JSON parsing: Gemini may occasionally return non-JSON responses despite instructions
- Context window: Very large PDFs may exceed Gemini's context limits

## Contributing

This is a personal productivity tool. Feel free to fork and customize for your own needs.

## License

MIT License - Feel free to use and modify as needed.

## Support

For issues with:
- **Gemini API**: Check [Google AI documentation](https://ai.google.dev/docs)
- **Streamlit**: Visit [Streamlit documentation](https://docs.streamlit.io/)
- **This application**: Review error messages and troubleshooting section above

---

**Built with:** Python | Streamlit | Google Gemini API | OpenPyXL

**Version:** 1.0.0
