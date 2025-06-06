import os
import requests
from dotenv import load_dotenv
from rich import print
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.text import Text
from datetime import datetime, timedelta
import calendar
import re

# Load environment variables
load_dotenv()

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"

# Initialize console
console = Console()

def get_rate_limit():
    """
    Get GitHub API rate limit information
    """
    try:
        headers = {
            'Authorization': f'token {os.getenv("GITHUB_TOKEN")}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = requests.get(f"{GITHUB_API_URL}/rate_limit", headers=headers)
        response.raise_for_status()
        rate_limit = response.json()
        return rate_limit["resources"]["core"]
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error fetching rate limit: {str(e)}[/red]")
        return None

def get_repo_info(repo_url):
    """
    Extract owner and repo name from GitHub URL
    """
    try:
        # Accept URLs like https://github.com/owner/repo or github.com/owner/repo
        match = re.search(r'github\.com[/:]([\w\-]+)/([\w\-.]+)', repo_url)
        if not match:
            raise ValueError("Invalid GitHub repository URL. Please provide a URL like https://github.com/owner/repo")
        owner = match.group(1)
        repo = match.group(2)
        # Disallow URLs that are just github.com or github.com/owner
        if not owner or not repo or repo.lower() in ["issues", "pulls", "projects", "wiki", "pulse", "graphs", "settings"]:
            raise ValueError("Invalid GitHub repository URL. Please provide a URL like https://github.com/owner/repo")
        return owner, repo
    except Exception as e:
        console.print(f"[red]Error parsing URL: {str(e)}[/red]")
        raise

def fetch_repo_data(owner, repo):
    """
    Fetch repository data from GitHub API
    """
    try:
        # Get GitHub token from environment variables
        github_token = os.getenv('GITHUB_TOKEN')
        
        # Create headers
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        # Add authorization header if token is available
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        # Get repository information
        with Progress(console=console) as progress:
            task = progress.add_task("[cyan]Fetching repository data...", total=1)
            
            repo_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
            response = requests.get(repo_url, headers=headers)
            response.raise_for_status()
            repo_data = response.json()
            
            # Get contributors (try /stats/contributors for large repos)
            contributors = []
            try:
                page = 1
                while True:
                    contributors_url = f"{repo_url}/contributors?per_page=100&page={page}"
                    contributors_response = requests.get(contributors_url, headers=headers)
                    if contributors_response.status_code == 403:
                        # Fallback to /stats/contributors for large repos
                        stats_url = f"{repo_url}/stats/contributors"
                        stats_response = requests.get(stats_url, headers=headers)
                        stats_response.raise_for_status()
                        stats_contributors = stats_response.json()
                        # Format to match expected contributor fields
                        for c in stats_contributors or []:
                            contributors.append({
                                'login': c.get('author', {}).get('login', 'N/A'),
                                'contributions': c.get('total', 0)
                            })
                        break
                    contributors_response.raise_for_status()
                    page_contributors = contributors_response.json()
                    if not page_contributors:
                        break
                    contributors.extend(page_contributors)
                    page += 1
            except Exception as e:
                console.print(f"[yellow]Could not fetch full contributor list: {str(e)}[/yellow]")
            # Get commits (first page only, as full history is too large for linux repo)
            commits_url = f"{repo_url}/commits?per_page=100"
            commits_response = requests.get(commits_url, headers=headers)
            commits_response.raise_for_status()
            commits = commits_response.json()
            
            progress.update(task, completed=1)
        
        return repo_data, contributors, commits
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error fetching repository data: {str(e)}[/red]")
        raise

def get_commit_stats(commits):
    """
    Calculate commit statistics
    """
    if not commits:
        return {
            "total": 0,
            "by_month": {},
            "by_day": {},
            "by_hour": {}
        }
    
    stats = {
        "total": len(commits),
        "by_month": {},
        "by_day": {},
        "by_hour": {}
    }
    
    for commit in commits:
        # Fix: Handle 'Z' at the end of ISO date string
        date_str = commit["commit"]["author"]["date"].replace("Z", "+00:00")
        commit_date = datetime.fromisoformat(date_str).replace(tzinfo=None)
        
        # Monthly stats
        month_key = f"{commit_date.year}-{commit_date.month:02d}"
        stats["by_month"][month_key] = stats["by_month"].get(month_key, 0) + 1
        
        # Daily stats
        day_key = commit_date.strftime("%A")
        stats["by_day"][day_key] = stats["by_day"].get(day_key, 0) + 1
        
        # Hourly stats
        hour_key = f"{commit_date.hour:02d}:00"
        stats["by_hour"][hour_key] = stats["by_hour"].get(hour_key, 0) + 1
    
    return stats

def display_repo_info(repo_data):
    """
    Display repository information in a formatted panel
    """
    info_table = Table(show_header=False, box=None)
    info_table.add_column(justify="right", style="cyan")
    info_table.add_column(style="white")
    
    info_table.add_row("Name:", repo_data.get("name", "N/A"))
    info_table.add_row("Description:", repo_data.get("description", "N/A"))
    info_table.add_row("Stars:", str(repo_data.get("stargazers_count", 0)))
    info_table.add_row("Forks:", str(repo_data.get("forks_count", 0)))
    info_table.add_row("Watchers:", str(repo_data.get("watchers_count", 0)))
    info_table.add_row("License:", repo_data.get("license", {}).get("name", "N/A"))
    info_table.add_row("Created:", repo_data.get("created_at", "N/A"))
    info_table.add_row("Last Updated:", repo_data.get("updated_at", "N/A"))
    
    console.print(Panel(info_table, title="[bold cyan]Repository Info[/bold cyan]", expand=False))

def display_contributors(contributors):
    """
    Display contributors in a formatted table
    """
    if not contributors:
        console.print("[yellow]No contributors found[/yellow]")
        return
    
    contrib_table = Table(title="[bold cyan]Contributors[/bold cyan]")
    contrib_table.add_column("Username", style="cyan")
    contrib_table.add_column("Contributions", style="white")
    
    for contributor in contributors:
        contrib_table.add_row(
            contributor.get("login", "N/A"),
            str(contributor.get("contributions", 0))
        )
    
    console.print(contrib_table)

def display_commit_stats(commit_stats):
    """
    Display commit statistics in various formats
    """
    if commit_stats["total"] == 0:
        console.print("[yellow]No commits found[/yellow]")
        return
    
    # Monthly commits
    monthly_table = Table(title="[bold cyan]Monthly Commit Activity[/bold cyan]")
    monthly_table.add_column("Month", style="cyan")
    monthly_table.add_column("Commits", style="white")
    
    for month, count in sorted(commit_stats["by_month"].items(), reverse=True):
        monthly_table.add_row(
            f"{calendar.month_name[int(month.split('-')[1])]} {month.split('-')[0]}",
            str(count)
        )
    
    console.print(monthly_table)
    
    # Daily commits
    daily_table = Table(title="[bold cyan]Daily Commit Activity[/bold cyan]")
    daily_table.add_column("Day", style="cyan")
    daily_table.add_column("Commits", style="white")
    
    for day, count in sorted(commit_stats["by_day"].items()):
        daily_table.add_row(day, str(count))
    
    console.print(daily_table)
    
    # Hourly commits
    hourly_table = Table(title="[bold cyan]Hourly Commit Activity[/bold cyan]")
    hourly_table.add_column("Hour", style="cyan")
    hourly_table.add_column("Commits", style="white")
    
    for hour, count in sorted(commit_stats["by_hour"].items()):
        hourly_table.add_row(hour, str(count))
    
    console.print(hourly_table)

# Dummy analyze_repository for GUI compatibility
# (The GUI does not use this, but import expects it)
def analyze_repository(*args, **kwargs):
    pass

def analyze_github_repo(owner, repo):
    """
    Fetch and return repository metadata, contributors, and recent commits for web/GUI use.
    """
    repo_data, contributors, commits = fetch_repo_data(owner, repo)
    commit_stats = get_commit_stats(commits)
    # Top 5 contributors
    top_contributors = [
        {
            'login': c.get('login', 'N/A'),
            'contributions': c.get('contributions', 0)
        } for c in contributors[:5]
    ] if contributors else []
    # Top 5 recent commits
    top_commits = [
        {
            'message': c.get('commit', {}).get('message', '').split('\n')[0],
            'author': c.get('commit', {}).get('author', {}).get('name', 'N/A'),
            'date': c.get('commit', {}).get('author', {}).get('date', 'N/A')
        } for c in commits[:5]
    ] if commits else []
    return {
        'name': repo_data.get('name', 'N/A'),
        'description': repo_data.get('description', 'N/A'),
        'stars': repo_data.get('stargazers_count', 0),
        'forks': repo_data.get('forks_count', 0),
        'watchers': repo_data.get('watchers_count', 0),
        'license': repo_data.get('license', {}).get('name', 'N/A'),
        'created_at': repo_data.get('created_at', 'N/A'),
        'updated_at': repo_data.get('updated_at', 'N/A'),
        'top_contributors': top_contributors,
        'commit_stats': commit_stats,
        'recent_commits': top_commits
    }

def main():
    """
    Main function to run the analyzer
    """
    console.print("[bold cyan]GitHub Repository Analyzer[/bold cyan]")
    
    # Check rate limit
    rate_limit = get_rate_limit()
    if rate_limit:
        remaining = rate_limit["remaining"]
        reset_time = datetime.fromtimestamp(rate_limit["reset"])
        console.print(f"[yellow]Rate limit: {remaining} requests remaining until {reset_time.strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
    
    # Get repository URL from command line argument
    import sys
    if len(sys.argv) < 2:
        console.print("[red]Please provide a GitHub repository URL as an argument[/red]")
        return
        
    repo_url = sys.argv[1]
    
    try:
        owner, repo = get_repo_info(repo_url)
        
        # Fetch data
        repo_data, contributors, commits = fetch_repo_data(owner, repo)
        
        # Calculate commit stats
        commit_stats = get_commit_stats(commits)
        
        # Display results
        display_repo_info(repo_data)
        display_contributors(contributors)
        display_commit_stats(commit_stats)
        
        # Display contributors (top 5)
        if contributors:
            console.print("\n[bold]Top Contributors:[/bold]")
            for i, contributor in enumerate(contributors[:5]):
                console.print(f"{i+1}. {contributor['login']} - {contributor['contributions']} contributions")
        
        # Display recent activity (top 5 commits)
        if commits:
            console.print("\n[bold]Recent Commits:[/bold]")
            for commit in commits[:5]:
                message = commit["commit"]["message"]
                author = commit["commit"]["author"]["name"]
                date = commit["commit"]["author"]["date"][:10]
                console.print(f"- {message} by {author} ({date})")
    
    except ValueError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {str(e)}[/red]")

if __name__ == "__main__":
    main()


