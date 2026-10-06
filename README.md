# Search Engine

![Architecture](architechture.png)

## Core Subsystems

* **Web Crawler:** Discovers HTML via a URL frontier, parses `robots.txt` (`urllib.robotparser`), and extracts links (`BeautifulSoup`). It enforces domain boundaries and timeouts.
* **Tokenizer:** Extracts alphanumeric words using regex `\b[a-zA-Z0-9]+\b`, lowercases them, and removes stop words (reducing index size by 30%).
* **Inverted Index:** Maps terms to document IDs and frequencies (`index[term][doc_id]`) in-memory for instant retrieval. 
* **Ranking (BM25):** Scores relevance using BM25 (k1=1.2, b=0.75) to balance Term Frequency, Inverse Document Frequency, and Document Length penalties (superior to simple TF-IDF).
* **CLI REPL:** Terminal interface that accepts queries, tokenizes input, and returns the top 5 results with snippets and scores.

## System Characteristics & Limitations

* **Performance:** Crawling 10 pages takes ~5-15 seconds. Can be optimized for concurrency using `asyncio` or thread pools.
* **Storage:** The index is purely in-memory (resets on exit), but can be easily exported to JSON/SQLite. Production systems use distributed SSD storage.
* **Ranking Logic:** Purely lexical. Lacks PageRank, reputation signals, or semantic AI embeddings. 
* **Matching:** Exact token match only. Unindexed terms are safely skipped. Lacks spelling correction and exact phrase searching (requires positional offsets).
* **Rendering:** Processes raw HTML only; cannot execute or render dynamic JavaScript (e.g., React/Vue).
* **Adaptability:** The crawler module can be swapped out to index local files using `pathlib` or `os`.
