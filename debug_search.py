from duckduckgo_search import DDGS
import json

with DDGS() as ddgs:
    results = [r for r in ddgs.news("technology", max_results=3)]
    print(json.dumps(results, indent=2))
