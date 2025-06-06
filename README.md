# GitHub Repository Analyzer (GUI Version)

A modern GUI application that analyzes GitHub repositories and provides comprehensive insights using the GitHub API.

## Features

- User-friendly graphical interface
- Two analysis modes:
  - Single Repository Analysis (via URL)
  - Batch Analysis (via Excel, PDF, or Word files)
- Detailed repository insights including:
  - Basic repository information (stars, forks, watchers)
  - Top contributors and their contributions
  - Language breakdown with percentages
  - Repository creation and last update dates
  - License information
  - Commit statistics
- Export analysis results
- Real-time progress updates
- Error handling and user feedback

## Installation

### Using Docker (Recommended)

1. Install Docker and Docker Compose
2. Build and run the application:
```bash
docker-compose up --build
```

### Local Installation

1. Install the required dependencies:
```bash
pip install -r requirements_gui.txt
```

## Usage

### Using Docker (Web Interface - Recommended)

1. Build and run the container:
```bash
   docker-compose up --build
```
2. Open your browser and go to: [http://localhost:8501](http://localhost:8501)
   - The Streamlit web interface will let you analyze single GitHub repo links or upload Excel, PDF, or DOCX files containing multiple repo URLs.

### Local Usage (GUI or Web)

1. Install the required dependencies:
```bash
pip install -r requirements_gui.txt
```
2. To run the classic desktop GUI (Tkinter):
```bash
python github_analyzer_gui.py
```
3. To run the web interface locally (Streamlit):
```bash
streamlit run github_analyzer_web.py
```
4. Use the interface to:
   - Analyze a single GitHub repository URL
   - Upload a file (Excel, PDF, DOCX) with multiple repo URLs
   - View and copy/export results

## Requirements

- Python 3.7+
- Docker (for containerized web interface)
- GitHub API rate limits apply (60 requests per hour for unauthenticated requests)

## API Rate Limits

For higher API rate limits, consider:
1. Creating a GitHub Personal Access Token
2. Adding it to a `.env` file with the key `GITHUB_TOKEN`
3. The tool will automatically use this token if available

## Supported File Formats

- Excel (.xlsx)
- PDF (.pdf)
- Word (.docx)

## Project Structure

- `github_analyzer.py`: Core logic for fetching and analyzing GitHub repository data
- `github_insights.py`: Additional insights and formatting for repositories
- `github_analyzer_gui.py`: Tkinter-based desktop GUI
- `github_analyzer_web.py`: Streamlit-based web interface (recommended)
- `Dockerfile`, `docker-compose.yml`: For containerized deployment
- `requirements.txt`, `requirements_gui.txt`: Dependency management

## Notes

- The web interface is the recommended way to use this tool, especially in Docker.
- For Docker, always access the app at [http://localhost:8501](http://localhost:8501).
- Both GUI and web versions support robust error handling and batch analysis from files.
