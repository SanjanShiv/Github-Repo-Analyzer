import requests
import os
from dotenv import load_dotenv
from colorama import init, Fore, Style
from tabulate import tabulate
import re
from datetime import datetime

# Initialize colorama for colored output
init()

# Load environment variables
load_dotenv()

# GitHub API base URL
GITHUB_API = "https://api.github.com"

def get_repo_info(repo_url):
    """Extract repository information from URL"""
    # Extract owner and repo name from URL
    match = re.search(r'github.com/([^/]+)/([^/]+)', repo_url)
    if not match:
        return None, None
    
    owner = match.group(1)
    repo = match.group(2)
    return owner, repo

def fetch_github_data(owner, repo):
    """Fetch data from GitHub API"""
    # Get GitHub token from environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    
    headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    # Add authorization header if token is available
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        # Get repository information
        repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
        repo_response = requests.get(repo_url, headers=headers)
        repo_response.raise_for_status()  # Raise an exception for bad status codes
        repo_data = repo_response.json()
        
        # Get contributors
        contributors_url = f"{repo_url}/contributors"
        contributors_response = requests.get(contributors_url, headers=headers)
        contributors_response.raise_for_status()
        contributors = contributors_response.json()
        
        # Get languages
        languages_url = f"{repo_url}/languages"
        languages_response = requests.get(languages_url, headers=headers)
        languages_response.raise_for_status()
        languages = languages_response.json()
        
        return repo_data, contributors, languages
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            # Rate limit exceeded
            rate_limit = e.response.headers.get('X-RateLimit-Remaining')
            reset_time = e.response.headers.get('X-RateLimit-Reset')
            if reset_time:
                reset_time = datetime.fromtimestamp(int(reset_time))
                print(f"{Fore.RED}Rate limit exceeded. Reset time: {reset_time}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Rate limit exceeded. Please wait before making more requests.{Style.RESET_ALL}")
        elif e.response.status_code == 404:
            print(f"{Fore.RED}Repository not found.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}HTTP Error: {e.response.status_code}{Style.RESET_ALL}")
        raise
    except Exception as e:
        print(f"{Fore.RED}Error fetching data: {str(e)}{Style.RESET_ALL}")
        raise

def format_contributors(contributors):
    """Format contributors data for display"""
    formatted = []
    for contributor in contributors:
        formatted.append([
            contributor.get('login', 'N/A'),
            contributor.get('contributions', 0)
        ])
    return formatted

def format_languages(languages):
    """Format languages data for display"""
    total_bytes = sum(languages.values())
    formatted = []
    for lang, bytes in languages.items():
        percentage = (bytes / total_bytes) * 100
        formatted.append([lang, f"{bytes:,}", f"{percentage:.1f}%"])
    return formatted

def delete_test_rate_limit():
    """Delete the test_rate_limit.py file if it exists."""
    file_path = os.path.join(os.path.dirname(__file__), 'test_rate_limit.py')
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"{Fore.YELLOW}Deleted test_rate_limit.py file.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Failed to delete test_rate_limit.py: {str(e)}{Style.RESET_ALL}")

def get_repo_insights(owner, repo):
    """
    Fetch and return repository insights (contributors, commit activity, recent commits) for web/GUI use.
    """
    repo_data, contributors, languages = fetch_github_data(owner, repo)
    # Format contributors
    formatted_contributors = [
        {
            'login': c.get('login', 'N/A'),
            'contributions': c.get('contributions', 0)
        } for c in contributors[:5]
    ] if contributors else []
    # Format languages
    total_bytes = sum(languages.values()) or 1
    formatted_languages = [
        {
            'language': lang,
            'bytes': bytes,
            'percentage': round((bytes / total_bytes) * 100, 1)
        } for lang, bytes in languages.items()
    ]
    # Recent commits (reuse fetch_github_data logic for repo_data)
    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=5"
    github_token = os.getenv('GITHUB_TOKEN')
    headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    commits = []
    try:
        resp = requests.get(commits_url, headers=headers)
        resp.raise_for_status()
        commits = resp.json()
    except Exception:
        pass
    formatted_commits = [
        {
            'message': c.get('commit', {}).get('message', '').split('\n')[0],
            'author': c.get('commit', {}).get('author', {}).get('name', 'N/A'),
            'date': c.get('commit', {}).get('author', {}).get('date', 'N/A')
        } for c in commits[:5]
    ] if commits else []
    return {
        'contributors': formatted_contributors,
        'languages': formatted_languages,
        'recent_commits': formatted_commits
    }

def main():
    print(f"{Fore.CYAN}GitHub Repository Insights Tool{Style.RESET_ALL}\n")
    
    repo_url = input("Enter GitHub repository URL: ")
    owner, repo = get_repo_info(repo_url)
    
    if not owner or not repo:
        print(f"{Fore.RED}Error: Invalid GitHub repository URL{Style.RESET_ALL}")
        return
    
    try:
        try:
            repo_data, contributors, languages = fetch_github_data(owner, repo)
            
            # Basic repository information
            print(f"\n{Fore.GREEN}Repository Information:{Style.RESET_ALL}")
            print(f"Name: {repo_data.get('name', 'N/A')}")
            print(f"Description: {repo_data.get('description', 'N/A')}")
            print(f"Stars: {repo_data.get('stargazers_count', 0)}")
            print(f"Forks: {repo_data.get('forks_count', 0)}")
            print(f"Watchers: {repo_data.get('watchers_count', 0)}")
            print(f"License: {repo_data.get('license', {}).get('name', 'N/A')}")
            print(f"Created: {repo_data.get('created_at', 'N/A')}")
            print(f"Last Updated: {repo_data.get('updated_at', 'N/A')}\n")
            
            # Contributors
            print(f"{Fore.GREEN}Top Contributors:{Style.RESET_ALL}")
            formatted_contributors = format_contributors(contributors)
            print(tabulate(formatted_contributors, headers=["Username", "Contributions"], tablefmt="grid"))
            
            # Languages
            print(f"\n{Fore.GREEN}Languages Used:{Style.RESET_ALL}")
            formatted_languages = format_languages(languages)
            print(tabulate(formatted_languages, headers=["Language", "Bytes", "Percentage"], tablefmt="grid"))
        except Exception as e:
            print(f"{Fore.RED}Error fetching data from GitHub API: {str(e)}{Style.RESET_ALL}")
        formatted_languages = format_languages(languages)
        print(tabulate(formatted_languages, headers=["Language", "Bytes", "Percentage"], tablefmt="grid"))
        
    except Exception as e:
        print(f"{Fore.RED}Error fetching data from GitHub API: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
    delete_test_rate_limit()
