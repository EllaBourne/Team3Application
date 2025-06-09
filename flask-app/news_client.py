import os
import requests

class NewsClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2/everything"

    def get_articles(self, stock_symbol, max_articles=5):
        params = {
            'q': stock_symbol,
            'sortBy': 'publishedAt',
            'language': 'en',
            'apiKey': self.api_key,
            'pageSize': max_articles
        }
        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            return response.json().get('articles', [])
        return []
