import aiohttp
import os
import fitz  # PyMuPDF
import re
import xml.etree.ElementTree as ET

class PaperHandler:
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.openalex_url = "https://api.openalex.org/works"
        self.arxiv_url = "http://export.arxiv.org/api/query"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self._session = None

    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def search_openalex(self, query):
        params = {
            "search": query,
            "filter": "has_fulltext:true,is_oa:true",
            "per_page": 5,  # Increased slightly for parallel processing demo
            "sort": "relevance_score:desc"
        }
        try:
            session = await self.get_session()
            async with session.get(self.openalex_url, params=params, headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()
                results = data.get("results", [])
                
                for paper in results:
                    inv_index = paper.get("abstract_inverted_index")
                    if inv_index:
                        try:
                            max_idx = max([max(pos) for pos in inv_index.values() if pos])
                            words = [""] * (max_idx + 1)
                            for word, positions in inv_index.items():
                                for pos in positions:
                                    words[pos] = word
                            paper["abstract"] = " ".join(words).strip()
                        except ValueError:
                            paper["abstract"] = ""
                    else:
                        paper["abstract"] = ""
                        
                return results
        except Exception as e:
            print(f"Error searching OpenAlex: {e}")
            return []

    async def search_arxiv(self, query):
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": 5,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        try:
            session = await self.get_session()
            async with session.get(self.arxiv_url, params=params, headers=self.headers) as response:
                response.raise_for_status()
                text = await response.text()
                
                root = ET.fromstring(text)
                namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                results = []
                
                for entry in root.findall('atom:entry', namespace):
                    title = entry.find('atom:title', namespace).text.strip()
                    summary = entry.find('atom:summary', namespace).text.strip()
                    paper_id = entry.find('atom:id', namespace).text.strip()
                    
                    pdf_url = ""
                    for link in entry.findall('atom:link', namespace):
                        if link.attrib.get('title') == 'pdf':
                            pdf_url = link.attrib.get('href')
                    
                    if not pdf_url:
                        pdf_url = paper_id.replace("abs", "pdf") + ".pdf"
                    
                    published = entry.find('atom:published', namespace).text
                    year = published.split('-')[0] if published else "Unknown"

                    results.append({
                        "id": paper_id,
                        "title": title,
                        "abstract": summary,
                        "year": year,
                        "authors": [a.find('atom:name', namespace).text for a in entry.findall('atom:author', namespace)],
                        "open_access": {"oa_url": pdf_url}
                    })
                return results
        except Exception as e:
            print(f"Error searching ArXiv: {e}")
            return []

    async def download_pdf(self, paper_url, paper_id, title=None, year=None):
        if title and year:
            # Sanitize title for filename
            clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
            filename = f"{clean_title} ({year}).pdf"
        else:
            filename = f"{paper_id.split('/')[-1]}.pdf"
            
        filepath = os.path.join(self.download_dir, filename)
        
        # Check if file exists AND is not empty
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath
            
        try:
            session = await self.get_session()
            async with session.get(paper_url, headers=self.headers, timeout=30) as response:
                response.raise_for_status()
                
                # Ensure the file is deleted if the download fails halfway or results in an empty file
                with open(filepath, "wb") as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            
            # Final check: if file is still empty, delete it
            if os.path.exists(filepath) and os.path.getsize(filepath) == 0:
                os.remove(filepath)
                return None
                
            return filepath
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            print(f"Error downloading PDF {paper_id}: {e}")
            return None

    def extract_text_and_chunk(self, pdf_path, tokens_per_chunk=2000):
        words_per_chunk = int(tokens_per_chunk * 0.75)
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"Error extracting text: {e}")
            return []

        words = text.split()
        return [" ".join(words[i:i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
