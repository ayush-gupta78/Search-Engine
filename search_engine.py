import collections
import math
import re
import urllib.parse
import urllib.robotparser
from bs4 import BeautifulSoup
import requests

STOP_WORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "by", "for",
    "from", "how", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "was", "what", "when", "where", "which", "with"
} # These words reduces index size by 30% & increases speed

def tokenize(text:str) -> list[str]:
    raw_tokens = re.findall(r"\b[a-zA-Z0-9]+\b",text.lower())
    return [t for t in raw_tokens if t not in STOP_WORDS]

class InvertedIndex:
    def __init__(self):
        self.index = collections.defaultdict(lambda: collections.defaultdict(int))
        self.doc_lengths = {}
        self.total_docs = 0
        
    def add_document(self, doc_id:str , tokens:list[str]) -> None:
        self.doc_lengths[doc_id]=len(tokens)
        for token in tokens:
            self.index[token][doc_id] +=1
        self.total_docs = len(self.doc_lengths)

    @property
    def avg_doc_length(self) -> float:
        if not self.doc_lengths:
            return 0.0
        return sum(self.doc_lengths.values()) /len(self.doc_lengths)

def crawl_domain(start_url:str , max_pages:int=15) -> dict[str,str]:
    domain = urllib.parse.urlparse(start_url).netloc
    scheme = urllib.parse.urlparse(start_url).scheme
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{scheme}://{domain}/robots.txt")
    try:
        rp.read()
    except Exception:
        pass

    visited = set()
    frontier = collections.deque([start_url])
    corpus = {}
    print(f"[*] Crawling up to {max_pages} pages from {domain}...")

    while frontier and len(corpus) < max_pages:
        url = frontier.popleft()
        if url in visited:
            continue
        visited.add(url)

        if not rp.can_fetch("MiniSearchBot", url):
            continue

        try:
            resp = requests.get(url, headers={"User-Agent": "MiniSearchBot/1.0"}, timeout=5)
            if resp.status_code != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = " ".join(soup.stripped_strings)
            corpus[url] = text
            print(f"  [+] Indexed: {url} ({len(text)} chars)")

            for a in soup.find_all("a", href=True):
                next_url = urllib.parse.urljoin(url, a["href"])
                next_url, _ = urllib.parse.urldefrag(next_url)
                if urllib.parse.urlparse(next_url).netloc == domain and next_url not in visited:
                    frontier.append(next_url)
        except Exception:
            continue
    return corpus

def score_bm25(query_tokens:list[str] , index:InvertedIndex , k1:float=1.2 , b:float=0.75) -> list[tuple[str,float]]: 
    #Robertson _Sparck Jones Formula with default paramteres
    scores = collections.defaultdict(float)
    avg_len = index.avg_doc_length

    for token in query_tokens:
        if token not in index.index:
            continue
        postings = index.index[token]
        idf = math.log((index.total_docs - len(postings) + 0.5) / (len(postings) + 0.5 ) + 1.0)

        for doc_id , tf in postings.items():
            doc_len = index.doc_lengths[doc_id]
            numerator = tf*(k1+1.0)
            denominator = tf +k1 * (1.0 - b + b* (doc_len / avg_len))
            scores[doc_id] += idf * (numerator / denominator)

    return sorted(scores.items() , key=lambda item: item[1], reverse=True)

def main():
    target = input("Enter URL").strip()
    if not target:
        target = "https://example.com" # If no input

    corpus = crawl_domain(target , max_pages=10)
    if not corpus:
        print("No documents")
        return

    index=InvertedIndex()
    for url , text in corpus.items():
        index.add_document(url,tokenize(text))

    print(f"\nSuccess : Indexed {index.total_docs} pages , {len(index.index)} terms")
    print("\nSearch engine is running \n Type 'exit' to quit")

    while True:
        try:
            q= input("Search:").strip()
            if not q or q.lower() =="exit":
                break

            results = score_bm25(tokenize(q) , index)
            if not results:
                print("No document found")
            print("Results for {q} :")
            for r , (url,score) in enumerate(results[:5] , start=1):
                snippet = corpus[url][:110].replace("\n","") + "..."
                print(f" {r} , [{score:.4f}] {url}\n   {snippet}")
        except (KeyboardInterrupt , EOFError):
            break
if __name__ == "__main__":
    main()
