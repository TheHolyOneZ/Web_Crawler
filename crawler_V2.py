import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
import requests
from concurrent.futures import ThreadPoolExecutor
from collections import deque

# Configure customtkinter theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Logging setup
logging.basicConfig(filename="crawler.log", level=logging.INFO, format="%(asctime)s %(message)s")


class WebCrawlerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Crawler V2 - TheZ")
        self.root.geometry("750x800")
        self.root.configure(bg="#1f1f1f")
        self.root.iconbitmap("icon.ico")
        self.root.resizable(False, False)

        # URL Entry
        self.url_label = ctk.CTkLabel(root, text="Enter URL:")
        self.url_label.pack(pady=10)
        self.url_entry = ctk.CTkEntry(root, width=400)
        self.url_entry.pack()

        # Depth Entry
        self.depth_label = ctk.CTkLabel(root, text="Depth (default: 3):")
        self.depth_label.pack(pady=10)
        self.depth_entry = ctk.CTkEntry(root, width=100)
        self.depth_entry.insert(0, "3")
        self.depth_entry.pack()

        # Number of Retries
        self.retries_label = ctk.CTkLabel(root, text="Retries (default: 3):")
        self.retries_label.pack(pady=10)
        self.retries_entry = ctk.CTkEntry(root, width=100)
        self.retries_entry.insert(0, "3")
        self.retries_entry.pack()

        # Number of Threads
        self.threads_label = ctk.CTkLabel(root, text="Threads (default: 3):")
        self.threads_label.pack(pady=10)
        self.threads_entry = ctk.CTkEntry(root, width=100)
        self.threads_entry.insert(0, "3")
        self.threads_entry.pack()

        # Toggle for Resource Download
        self.download_enabled = ctk.BooleanVar(value=False)
        self.download_toggle = ctk.CTkCheckBox(root, text="Download HTML/CSS/JS/Images", variable=self.download_enabled)
        self.download_toggle.pack(pady=10)

        # Start Crawl Button
        self.crawl_button = ctk.CTkButton(root, text="Start Crawling", command=self.start_crawling)
        self.crawl_button.pack(pady=20)

        # Results Box
        self.result_box = ctk.CTkTextbox(root, width=600, height=300)
        self.result_box.pack(pady=10)

        # Save Button
        self.save_button = ctk.CTkButton(root, text="Save Results", command=self.save_results)
        self.save_button.pack(pady=10)

        self.crawled_links = []
        self.to_download = []

    def validate_url(self, url):
        """Ensure the URL starts with https://"""
        if not url.startswith(("http://", "https://")):
            return "https://" + url
        return url

    async def fetch_links(self, session, url, base_url):
        """Fetch links and resources from the given URL."""
        try:
            async with session.get(url, timeout=10) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract links
                links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]

                # Download resources if enabled
                if self.download_enabled.get():
                    # Save main HTML
                    self.save_html(url, html)

                    # Download CSS files
                    for css in soup.find_all("link", rel="stylesheet"):
                        css_url = urljoin(base_url, css["href"])
                        self.to_download.append((css_url, "css"))

                    # Download JS files
                    for script in soup.find_all("script", src=True):
                        js_url = urljoin(base_url, script["src"])
                        self.to_download.append((js_url, "js"))

                    # Download images
                    for img in soup.find_all("img", src=True):
                        img_url = urljoin(base_url, img["src"])
                        self.to_download.append((img_url, "images"))

                return links
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return []

    def save_html(self, url, content):
        """Save the HTML content of the URL."""
        filename = self.generate_filename(url, "html", subfolder="html")
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
        logging.info(f"Saved HTML: {filename}")

    def save_file(self, url, content, file_type):
        """Save downloaded file content."""
        filename = self.generate_filename(url, file_type, subfolder=file_type)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as file:
            file.write(content)
        logging.info(f"Saved {file_type.upper()}: {filename}")

    def generate_filename(self, url, file_type, subfolder=""):
        """Generate a filename based on the URL and file type."""
        parsed_url = urlparse(url)
        filename = parsed_url.netloc + parsed_url.path.replace("/", "_")
        if not filename.endswith(f".{file_type}"):
            filename += f".{file_type}"
        return os.path.join("downloads", subfolder, filename)

    async def crawl(self, url, depth, retries, threads):
        """Crawl the website up to the specified depth."""
        async with aiohttp.ClientSession() as session:
            to_crawl = deque([url])
            visited = set()

            for _ in range(depth):
                if not to_crawl:
                    break

                tasks = []
                for _ in range(min(len(to_crawl), threads)):
                    current_url = to_crawl.popleft()
                    if current_url in visited:
                        continue
                    visited.add(current_url)
                    tasks.append(self.fetch_links(session, current_url, url))

                results = await asyncio.gather(*tasks)
                for links in results:
                    for link in links:
                        if link not in visited:
                            to_crawl.append(link)
                            self.crawled_links.append(link)

            # Download all resources after crawling
            if self.download_enabled.get():
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    for url, file_type in self.to_download:
                        executor.submit(self.download_resource, url, file_type)

    def download_resource(self, url, file_type):
        """Download a single resource (CSS, JS, Images)."""
        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.save_file(url, response.content, file_type)
                    return
            except Exception as e:
                logging.error(f"Error downloading {file_type} from {url}: {e}")
                if attempt == 2:
                    logging.error(f"Failed after 3 attempts: {url}")

    def start_crawling(self):
        """Start the crawling process."""
        url = self.validate_url(self.url_entry.get())
        try:
            depth = int(self.depth_entry.get())
            retries = int(self.retries_entry.get())
            threads = int(self.threads_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Depth, retries, and threads must be integers.")
            return

        self.crawled_links = []
        self.to_download = []

        # Start asyncio loop
        asyncio.run(self.crawl(url, depth, retries, threads))

        # Display results
        self.result_box.insert(ctk.END, "Crawled Links:\n" + "\n".join(self.crawled_links))

    def save_results(self):
        """Save the crawled links."""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w") as file:
                file.write("\n".join(self.crawled_links))
            messagebox.showinfo("Success", f"Results saved to {file_path}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = WebCrawlerApp(root)
    root.mainloop()
