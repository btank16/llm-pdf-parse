"""
PDF Analyzer with Gemini 3 Pro - Streamlit Application

A desktop application for batch analyzing PDF files using Google's Gemini API
and exporting structured results to Excel.
"""

import streamlit as st
import os
import json
import pathlib
from typing import List, Dict, Any
from dotenv import load_dotenv

from gemini_client import GeminiPDFAnalyzer, validate_api_key
from prompt_builder import build_analysis_prompt, get_default_prompt
from excel_export import create_excel_file, format_results_for_export

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="PDF Analyzer with Gemini",
    page_icon="📄",
    layout="wide"
)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'columns' not in st.session_state:
        st.session_state.columns = ["Document Name"]

    if 'prompt_text' not in st.session_state:
        st.session_state.prompt_text = get_default_prompt()

    if 'results' not in st.session_state:
        st.session_state.results = []

    if 'filenames' not in st.session_state:
        st.session_state.filenames = []

    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = []


def add_column():
    """Add a new column to the column list."""
    new_col_name = st.session_state.get('new_column_input', '').strip()
    if new_col_name and new_col_name not in st.session_state.columns:
        st.session_state.columns.append(new_col_name)
        st.session_state.new_column_input = ""


def remove_column(col_name: str):
    """Remove a column from the column list."""
    if col_name in st.session_state.columns and col_name != "Document Name":
        st.session_state.columns.remove(col_name)


def save_template():
    """Save current prompt and columns as a JSON template."""
    template = {
        "prompt": st.session_state.prompt_text,
        "columns": [col for col in st.session_state.columns if col != "Document Name"]
    }

    template_json = json.dumps(template, indent=2)
    st.download_button(
        label="💾 Download Template",
        data=template_json,
        file_name="pdf_analysis_template.json",
        mime="application/json",
        key="download_template"
    )


def load_template(uploaded_file):
    """Load prompt and columns from a JSON template file."""
    try:
        template = json.load(uploaded_file)
        st.session_state.prompt_text = template.get("prompt", get_default_prompt())

        loaded_columns = template.get("columns", [])
        st.session_state.columns = ["Document Name"] + loaded_columns

        st.success("Template loaded successfully!")
    except Exception as e:
        st.error(f"Error loading template: {str(e)}")


def collect_pdfs_from_folder(folder_path: str) -> List[tuple]:
    """
    Recursively find all PDF files in a folder.

    Args:
        folder_path: Path to folder

    Returns:
        List of tuples (file_path, filename, file_bytes)
    """
    pdf_files = []
    path = pathlib.Path(folder_path)

    if not path.exists():
        st.error(f"Folder path does not exist: {folder_path}")
        return []

    if not path.is_dir():
        st.error(f"Path is not a directory: {folder_path}")
        return []

    for pdf_path in path.rglob("*.pdf"):
        try:
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
                pdf_files.append((str(pdf_path), pdf_path.name, pdf_bytes))
        except Exception as e:
            st.warning(f"Could not read {pdf_path.name}: {str(e)}")

    return pdf_files


def analyze_pdfs(
    pdf_files: List[tuple],
    analyzer: GeminiPDFAnalyzer,
    prompt_text: str,
    column_names: List[str]
):
    """
    Analyze multiple PDF files and update results in session state.

    Args:
        pdf_files: List of tuples (file_path, filename, file_bytes)
        analyzer: GeminiPDFAnalyzer instance
        prompt_text: User's analysis prompt
        column_names: List of output column names
    """
    # Build the complete prompt
    full_prompt = build_analysis_prompt(prompt_text, column_names)

    # Reset results
    st.session_state.results = []
    st.session_state.filenames = []
    st.session_state.processing_status = []

    # Progress tracking
    progress_bar = st.progress(0)
    status_container = st.container()

    for idx, (file_path, filename, pdf_bytes) in enumerate(pdf_files):
        # Update progress
        progress = (idx) / len(pdf_files)
        progress_bar.progress(progress)

        # Show current file being processed
        with status_container:
            st.info(f"⏳ Processing: {filename}")

        # Analyze PDF
        success, result_dict, error_msg = analyzer.analyze_pdf(
            pdf_bytes=pdf_bytes,
            filename=filename,
            prompt=full_prompt
        )

        # Store results
        st.session_state.filenames.append(filename)

        if success:
            st.session_state.results.append(result_dict)
            st.session_state.processing_status.append(("✅", "Success"))
            with status_container:
                st.success(f"✅ Completed: {filename}")
        else:
            st.session_state.results.append({"Error": error_msg})
            st.session_state.processing_status.append(("❌", error_msg))
            with status_container:
                st.error(f"❌ Failed: {filename} - {error_msg}")

    # Complete progress
    progress_bar.progress(1.0)
    st.success(f"Analysis complete! Processed {len(pdf_files)} files.")


def main():
    """Main application logic."""
    initialize_session_state()

    st.title("📄 PDF Analyzer with Gemini 3 Pro")
    st.markdown("Batch analyze PDF files using AI and export structured results to Excel")

    # Sidebar - Settings
    with st.sidebar:
        st.header("⚙️ Settings")

        # API Key validation
        is_valid, api_key = validate_api_key()
        if is_valid:
            st.success("✅ API Key Found")
        else:
            st.error("❌ GEMINI_API_KEY not set in environment")
            st.info("Set the GEMINI_API_KEY environment variable or create a .env file")
            st.stop()

        # Model selection
        model = st.selectbox(
            "Model",
            options=["gemini-3-pro-preview", "gemini-2.5-flash"],
            help="gemini-2.5-flash is faster and cheaper, gemini-3-pro-preview is more capable"
        )

        # API delay
        api_delay = st.slider(
            "API Delay (seconds)",
            min_value=0.0,
            max_value=5.0,
            value=1.0,
            step=0.5,
            help="Delay between API requests to avoid rate limiting"
        )

        # Max retries
        max_retries = st.number_input(
            "Max Retries",
            min_value=0,
            max_value=5,
            value=2,
            help="Number of retry attempts for failed requests"
        )

        st.divider()

        # Template management
        st.subheader("📋 Templates")

        # Save template
        if st.button("💾 Save Current Configuration"):
            save_template()

        # Load template
        uploaded_template = st.file_uploader(
            "Load Template",
            type=['json'],
            help="Upload a previously saved template JSON file"
        )
        if uploaded_template:
            load_template(uploaded_template)

    # Main content area - 3 tabs
    tab1, tab2, tab3 = st.tabs(["📝 Configure", "▶️ Analyze", "📊 Results"])

    # TAB 1: Configuration
    with tab1:
        st.header("Configuration")

        # Column definition
        st.subheader("Define Output Columns")
        st.markdown("The first column **Document Name** is automatically populated with the PDF filename.")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(
                "Add New Column",
                key="new_column_input",
                placeholder="e.g., Contract Type, Effective Date, Key Terms"
            )
        with col2:
            st.button("➕ Add Column", on_click=add_column, use_container_width=True)

        # Display current columns
        st.markdown("**Current Columns:**")
        for col_name in st.session_state.columns:
            col_row1, col_row2 = st.columns([4, 1])
            with col_row1:
                if col_name == "Document Name":
                    st.text(f"📌 {col_name} (auto-populated)")
                else:
                    st.text(f"• {col_name}")
            with col_row2:
                if col_name != "Document Name":
                    st.button(
                        "🗑️",
                        key=f"remove_{col_name}",
                        on_click=remove_column,
                        args=(col_name,),
                        help=f"Remove {col_name}"
                    )

        st.divider()

        # Prompt editor
        st.subheader("Analysis Prompt")
        st.markdown("Define what you want Gemini to extract from each PDF:")

        st.session_state.prompt_text = st.text_area(
            "Prompt",
            value=st.session_state.prompt_text,
            height=250,
            help="This prompt will be sent to Gemini along with each PDF"
        )

        if st.button("↺ Reset to Default Prompt"):
            st.session_state.prompt_text = get_default_prompt()
            st.rerun()

    # TAB 2: Analyze
    with tab2:
        st.header("Analyze PDFs")

        # PDF input methods
        st.subheader("Select PDF Files")

        input_method = st.radio(
            "Input Method",
            options=["Upload Files", "Folder Path"],
            horizontal=True
        )

        pdf_files = []

        if input_method == "Upload Files":
            uploaded_files = st.file_uploader(
                "Upload PDF files",
                type=['pdf'],
                accept_multiple_files=True,
                help="Select one or more PDF files to analyze"
            )

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    pdf_bytes = uploaded_file.read()
                    pdf_files.append((None, uploaded_file.name, pdf_bytes))

                st.success(f"✅ {len(pdf_files)} file(s) uploaded")

        else:  # Folder Path
            folder_path = st.text_input(
                "Folder Path",
                placeholder="C:/Users/YourName/Documents/PDFs",
                help="Enter the full path to a folder containing PDF files"
            )

            if folder_path:
                if st.button("🔍 Scan Folder"):
                    with st.spinner("Scanning for PDF files..."):
                        pdf_files = collect_pdfs_from_folder(folder_path)

                    if pdf_files:
                        st.success(f"✅ Found {len(pdf_files)} PDF file(s)")
                        with st.expander("View files"):
                            for _, filename, _ in pdf_files:
                                st.text(f"• {filename}")
                    else:
                        st.warning("No PDF files found in the specified folder")

        st.divider()

        # Analyze button
        if pdf_files:
            # Validation
            custom_columns = [col for col in st.session_state.columns if col != "Document Name"]
            if not custom_columns:
                st.warning("⚠️ Add at least one output column in the Configure tab before analyzing")
            elif not st.session_state.prompt_text.strip():
                st.warning("⚠️ Enter an analysis prompt in the Configure tab before analyzing")
            else:
                if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                    # Create analyzer
                    analyzer = GeminiPDFAnalyzer(
                        api_key=api_key,
                        model=model,
                        max_retries=max_retries,
                        api_delay=api_delay
                    )

                    # Run analysis
                    with st.spinner("Analyzing PDFs..."):
                        analyze_pdfs(
                            pdf_files=pdf_files,
                            analyzer=analyzer,
                            prompt_text=st.session_state.prompt_text,
                            column_names=st.session_state.columns
                        )

                    # Switch to results tab
                    st.rerun()

    # TAB 3: Results
    with tab3:
        st.header("Analysis Results")

        if st.session_state.results:
            # Format results for display and export
            formatted_results = format_results_for_export(
                results=st.session_state.results,
                filenames=st.session_state.filenames,
                column_names=st.session_state.columns
            )

            # Display results table
            st.dataframe(
                formatted_results,
                use_container_width=True,
                height=400
            )

            # Processing status summary
            st.subheader("Processing Status")
            for filename, (status_icon, status_msg) in zip(
                st.session_state.filenames,
                st.session_state.processing_status
            ):
                if status_icon == "✅":
                    st.success(f"{status_icon} {filename}: {status_msg}")
                else:
                    st.error(f"{status_icon} {filename}: {status_msg}")

            st.divider()

            # Export to Excel
            st.subheader("Export Results")

            try:
                excel_bytes = create_excel_file(
                    results=formatted_results,
                    column_names=st.session_state.columns
                )

                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_bytes,
                    file_name="pdf_analysis_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"Error creating Excel file: {str(e)}")

            # Clear results button
            if st.button("🗑️ Clear Results"):
                st.session_state.results = []
                st.session_state.filenames = []
                st.session_state.processing_status = []
                st.rerun()

        else:
            st.info("No results yet. Configure your analysis and upload PDFs in the other tabs.")


if __name__ == "__main__":
    main()
