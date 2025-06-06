import streamlit as st
import pandas as pd
import re
import requests
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
from github_analyzer import analyze_github_repo
from github_insights import get_repo_insights

st.set_page_config(page_title="GitHub Analyzer Web", layout="wide")
st.title("GitHub Repository Analyzer (Web)")

MODE_SINGLE = "Single Link"
MODE_FILE = "File Upload"

mode = st.radio("Select Mode", [MODE_SINGLE, MODE_FILE])

repo_urls = set()

# Helper functions
def extract_github_links_from_text(text):
    # Match full GitHub repo URLs (with or without trailing slash)
    pattern = r"https?://github\.com/[\w\-]+/[\w\-.]+/?"
    return set(re.findall(pattern, text))

def extract_github_links_from_pdf(file):
    reader = PdfReader(file)
    links = set()
    for page in reader.pages:
        text = page.extract_text() or ""
        links.update(extract_github_links_from_text(text))
    return links

def extract_github_links_from_docx(file):
    doc = Document(file)
    text = " ".join([p.text for p in doc.paragraphs])
    return extract_github_links_from_text(text)

def extract_github_links_from_excel(file):
    df = pd.read_excel(file, engine="openpyxl")
    links = set()
    for col in df.columns:
        for val in df[col].astype(str):
            links.update(extract_github_links_from_text(val))
    return links

def analyze_and_display(owner, repo):
    try:
        meta = analyze_github_repo(owner, repo)
        insights = get_repo_insights(owner, repo)
        st.subheader(f"{owner}/{repo}")
        st.json(meta)
        # Only show unique info from insights (e.g., languages)
        if "languages" in insights:
            st.write("**Languages:**", insights["languages"])
        st.markdown("---")
        return meta, insights
    except Exception as e:
        st.error(f"Error analyzing {owner}/{repo}: {e}")
        return None, None

output_text = ""

if mode == MODE_SINGLE:
    url = st.text_input("Enter GitHub Repository URL:")
    if st.button("Analyze") and url:
        # Use the same regex as get_repo_info in github_analyzer.py
        match = re.match(r"https?://github\.com/([\w\-]+)/([\w\-.]+)", url)
        if match:
            owner, repo = match.groups()
            meta, insights = analyze_and_display(owner, repo)
            if meta and insights:
                output_text = f"{owner}/{repo}\nMeta: {meta}\nInsights: {insights}"
        else:
            st.error("Invalid GitHub repository URL.")
else:
    uploaded_file = st.file_uploader("Upload Excel, PDF, or DOCX file", type=["xlsx", "pdf", "docx"])
    if uploaded_file:
        if uploaded_file.name.endswith(".pdf"):
            links = extract_github_links_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            links = extract_github_links_from_docx(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            links = extract_github_links_from_excel(uploaded_file)
        else:
            links = set()
        if not links:
            st.warning("No GitHub repository links found in the file.")
        else:
            st.info(f"Found {len(links)} unique GitHub repositories.")
            for url in list(links)[:500]:
                match = re.match(r"https?://github\.com/([\w\-]+)/([\w\-.]+)", url)
                if match:
                    owner, repo = match.groups()
                    meta, insights = analyze_and_display(owner, repo)
                    if meta and insights:
                        output_text += f"{owner}/{repo}\nMeta: {meta}\nInsights: {insights}\n\n"

if output_text:
    st.download_button("Copy Output", output_text, file_name="github_analysis.txt")
