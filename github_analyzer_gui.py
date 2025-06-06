import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from github_analyzer import analyze_repository, get_repo_info, fetch_repo_data, get_commit_stats
from rich.console import Console
import threading
import queue
import json
import PyPDF2
import re

class GitHubAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Repository Analyzer")
        self.root.geometry("900x650")
        # Main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Title
        title = ttk.Label(self.main_frame, text="GitHub Repository Analyzer", font=("Arial", 18, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=10)
        # Mode selection
        self.mode = tk.StringVar(value="url")
        url_btn = ttk.Radiobutton(self.main_frame, text="Single Link", variable=self.mode, value="url", command=self.switch_mode)
        file_btn = ttk.Radiobutton(self.main_frame, text="Upload File", variable=self.mode, value="file", command=self.switch_mode)
        url_btn.grid(row=1, column=0, sticky=tk.W, padx=5)
        file_btn.grid(row=1, column=1, sticky=tk.W, padx=5)
        # URL input widgets
        self.url_frame = ttk.Frame(self.main_frame)
        self.url_label = ttk.Label(self.url_frame, text="Enter GitHub Repository URL:")
        self.url_entry = ttk.Entry(self.url_frame, width=60)
        self.url_analyze_btn = ttk.Button(self.url_frame, text="Analyze", command=self.analyze_url)
        self.url_label.grid(row=0, column=0, padx=5, pady=5)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)
        self.url_analyze_btn.grid(row=0, column=2, padx=5, pady=5)
        # File input widgets
        self.file_frame = ttk.Frame(self.main_frame)
        self.file_type = tk.StringVar(value="excel")
        ttk.Label(self.file_frame, text="File Type:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(self.file_frame, text="Excel", variable=self.file_type, value="excel").grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(self.file_frame, text="PDF", variable=self.file_type, value="pdf").grid(row=0, column=2, padx=5, pady=5)
        ttk.Radiobutton(self.file_frame, text="Word (DOCX)", variable=self.file_type, value="docx").grid(row=0, column=3, padx=5, pady=5)
        self.file_path = ttk.Entry(self.file_frame, width=50)
        self.file_path.grid(row=1, column=0, columnspan=4, padx=5, pady=5)
        self.browse_btn = ttk.Button(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_btn.grid(row=1, column=4, padx=5, pady=5)
        self.file_analyze_btn = ttk.Button(self.file_frame, text="Analyze URLs", command=self.analyze_file)
        self.file_analyze_btn.grid(row=2, column=0, columnspan=4, pady=10)
        # Results area
        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        self.results_text = tk.Text(self.results_frame, height=20, width=100)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.results_text.configure(state='disabled')
        self.copy_btn = ttk.Button(self.results_frame, text="Copy Output", command=self.copy_output)
        self.copy_btn.grid(row=1, column=0, sticky=tk.W, pady=5)
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        # Queue for thread-safe updates
        self.queue = queue.Queue()
        self.console = Console()
        self.switch_mode()

    def switch_mode(self):
        if self.mode.get() == "url":
            self.file_frame.grid_forget()
            self.url_frame.grid(row=2, column=0, columnspan=2, pady=10)
            # Clear results when switching to single link mode
            self.update_results("", replace=True)
        else:
            self.url_frame.grid_forget()
            self.file_frame.grid(row=2, column=0, columnspan=2, pady=10)
            # Do NOT clear results when switching to file mode

    def browse_file(self):
        # Dynamically set filetypes based on selected radio button
        if self.file_type.get() == "excel":
            filetypes = [("Excel files", "*.xlsx *.xls"), ("All files", "*")]
        elif self.file_type.get() == "pdf":
            filetypes = [("PDF files", "*.pdf"), ("All files", "*")]
        elif self.file_type.get() == "docx":
            filetypes = [("Word files", "*.docx"), ("All files", "*")]
        else:
            filetypes = [("All files", "*")]
        filename = filedialog.askopenfilename(title="Select file", filetypes=filetypes)
        if filename:
            self.file_path.delete(0, tk.END)
            self.file_path.insert(0, filename)

    def update_results(self, message, replace=False):
        self.results_text.configure(state='normal')
        if replace:
            self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.configure(state='disabled')
        self.results_text.see(tk.END)

    def analyze_url(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        # Clear previous output before analyzing new link
        self.update_results("", replace=True)
        threading.Thread(target=self._analyze_url_thread, args=(url,), daemon=True).start()

    def _analyze_url_thread(self, url):
        try:
            owner, repo = get_repo_info(url)
            repo_data, contributors, commits = fetch_repo_data(owner, repo)
            commit_stats = get_commit_stats(commits)
            results = []
            results.append(f"\nGitHub Repository Analysis\n")
            results.append(f"Repository: {owner}/{repo}\n")
            results.append("\nRepository Info:")
            results.append(f"Stars: {repo_data.get('stargazers_count', 0)}")
            results.append(f"Forks: {repo_data.get('forks_count', 0)}")
            results.append(f"Watchers: {repo_data.get('watchers_count', 0)}")
            results.append(f"License: {repo_data.get('license', {}).get('name', 'N/A')}")
            # Top contributors
            if contributors:
                results.append("\nTop Contributors:")
                for i, contrib in enumerate(contributors[:5]):
                    results.append(f"{i+1}. {contrib.get('login', 'N/A')} - {contrib.get('contributions', 0)} contributions")
            # Commit activity
            if commit_stats['total'] > 0:
                results.append(f"\nCommit Activity:")
                results.append(f"Total commits: {commit_stats['total']}")
                # Monthly
                if commit_stats['by_month']:
                    results.append("\nMonthly commits:")
                    for month, count in sorted(commit_stats['by_month'].items(), reverse=True)[:6]:
                        year, m = month.split('-')
                        import calendar
                        month_name = calendar.month_name[int(m)]
                        results.append(f"{month_name} {year}: {count}")
                # Daily
                if commit_stats['by_day']:
                    results.append("\nCommits by day:")
                    for day, count in sorted(commit_stats['by_day'].items()):
                        results.append(f"{day}: {count}")
                # Top 5 recent commits
                if commits:
                    results.append("\nTop 5 Recent Commits:")
                    for c in commits[:5]:
                        msg = c.get('commit', {}).get('message', '').split('\n')[0]
                        author = c.get('commit', {}).get('author', {}).get('name', 'N/A')
                        date = c.get('commit', {}).get('author', {}).get('date', 'N/A')
                        results.append(f"- {msg} (by {author} on {date})")
            self.queue.put(("\n".join(results), True))
        except Exception as e:
            self.queue.put((f"Error: {str(e)}", True))
        self.root.after(100, self.process_queue)

    def process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if isinstance(item, tuple):
                    message, replace = item
                    self.update_results(message, replace=replace)
                else:
                    self.update_results(item)
        except queue.Empty:
            self.root.after(100, self.process_queue)

    def analyze_file(self):
        filepath = self.file_path.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a file")
            return
        if not os.path.exists(filepath):
            messagebox.showerror("Error", "File not found")
            return
        threading.Thread(target=self._analyze_file_thread, args=(filepath,), daemon=True).start()

    def _analyze_file_thread(self, filepath):
        try:
            urls = []
            if filepath.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(filepath)
                urls = df.iloc[:, 0].dropna().astype(str).tolist()
            elif filepath.lower().endswith(".pdf"):
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            # Extract all github.com/owner/repo links from both hyperlinks and visible text
                            # 1. Find all github.com/owner/repo in the text
                            urls_in_page = re.findall(r'github\.com/([\w\-]+)/([\w\-]+)', text)
                            for owner, repo in urls_in_page:
                                urls.append(f"https://github.com/{owner}/{repo}")
                            # 2. Also try to extract from hyperlinks (if any)
                            if hasattr(page, 'annotations') and page.annotations:
                                for annot in page.annotations:
                                    uri = getattr(annot, 'uri', None)
                                    if uri and 'github.com' in uri:
                                        match = re.search(r'github\.com/([\w\-]+)/([\w\-]+)', uri)
                                        if match:
                                            owner, repo = match.groups()
                                            urls.append(f"https://github.com/{owner}/{repo}")
            elif filepath.lower().endswith(('.docx',)):
                import docx
                doc = docx.Document(filepath)
                for para in doc.paragraphs:
                    text = para.text
                    # Extract all github.com/owner/repo links from the visible text
                    urls_in_para = re.findall(r'github\.com/([\w\-]+)/([\w\-]+)', text)
                    for owner, repo in urls_in_para:
                        urls.append(f"https://github.com/{owner}/{repo}")
            else:
                raise ValueError("Unsupported file type")
            # Remove duplicates and limit to 500 links
            urls = list(dict.fromkeys(urls))[:500]
            self.queue.put((f"\nAnalyzing {len(urls)} repositories...", True))
            for idx, url in enumerate(urls, 1):
                try:
                    owner, repo = get_repo_info(url)
                    repo_data, contributors, commits = fetch_repo_data(owner, repo)
                    commit_stats = get_commit_stats(commits)
                    results = []
                    results.append(f"\nGitHub Repository Analysis [{idx}/{len(urls)}]\n")
                    results.append(f"Repository: {owner}/{repo}\n")
                    results.append("\nRepository Info:")
                    results.append(f"Stars: {repo_data.get('stargazers_count', 0)}")
                    results.append(f"Forks: {repo_data.get('forks_count', 0)}")
                    results.append(f"Watchers: {repo_data.get('watchers_count', 0)}")
                    results.append(f"License: {repo_data.get('license', {}).get('name', 'N/A')}")
                    # Top contributors
                    if contributors:
                        results.append("\nTop Contributors:")
                        for i, contrib in enumerate(contributors[:5]):
                            results.append(f"{i+1}. {contrib.get('login', 'N/A')} - {contrib.get('contributions', 0)} contributions")
                    # Commit activity
                    if commit_stats['total'] > 0:
                        results.append(f"\nCommit Activity:")
                        results.append(f"Total commits: {commit_stats['total']}")
                        # Monthly
                        if commit_stats['by_month']:
                            results.append("\nMonthly commits:")
                            for month, count in sorted(commit_stats['by_month'].items(), reverse=True)[:6]:
                                year, m = month.split('-')
                                import calendar
                                month_name = calendar.month_name[int(m)]
                                results.append(f"{month_name} {year}: {count}")
                        # Daily
                        if commit_stats['by_day']:
                            results.append("\nCommits by day:")
                            for day, count in sorted(commit_stats['by_day'].items()):
                                results.append(f"{day}: {count}")
                        # Top 5 recent commits
                        if commits:
                            results.append("\nTop 5 Recent Commits:")
                            for c in commits[:5]:
                                msg = c.get('commit', {}).get('message', '').split('\n')[0]
                                author = c.get('commit', {}).get('author', {}).get('name', 'N/A')
                                date = c.get('commit', {}).get('author', {}).get('date', 'N/A')
                                results.append(f"- {msg} (by {author} on {date})")
                    self.queue.put(("\n".join(results), False))
                except Exception as e:
                    self.queue.put((f"Error analyzing {url}: {str(e)}", False))
        except Exception as e:
            self.queue.put((f"Error: {str(e)}", True))
        self.root.after(100, self.process_queue)

    def copy_output(self):
        self.root.clipboard_clear()
        text = self.results_text.get(1.0, tk.END).strip()
        self.root.clipboard_append(text)
        self.root.update()  # Keeps clipboard after window closes

def main():
    root = tk.Tk()
    app = GitHubAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
