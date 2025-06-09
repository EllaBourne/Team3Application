from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import yfinance as yf
import requests
from news_client import NewsClient
from sentiment import analyze_articles
from helpers import validate_ticker, format_sentiment_summary, generate_natural_language_summary

app = Flask(__name__)

NEWS_API_KEY = 'd4b6777932da4e32ba9d8972d1aa7984'  # Replace with your actual key

def get_stock_news(stock_symbol):
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={stock_symbol}&"
        f"sortBy=publishedAt&"
        f"language=en&"
        f"apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get('articles', [])[:5]
        return articles
    return []

@app.route('/', methods=['GET', 'POST'])
def home():
    error = None
    articles = []
    summary = None
    sentiment_counts = None
    stock_symbol = ''
    nl_summary = None
    if request.method == 'POST':
        stock_symbol = request.form.get('stock_symbol', '').upper().strip()
        if not validate_ticker(stock_symbol):
            error = 'Invalid ticker symbol.'
        else:
            client = NewsClient()
            fetched_articles = client.get_articles(stock_symbol)
            # Fix: fallback to get_stock_news if NewsClient returns nothing
            if not fetched_articles:
                fetched_articles = get_stock_news(stock_symbol)
            if not fetched_articles:
                error = 'No news articles found.'
            else:
                articles, sentiment_counts = analyze_articles(fetched_articles)
                summary = format_sentiment_summary(sentiment_counts)
                # Add natural language summary
                nl_summary = generate_natural_language_summary(articles)
    return render_template('home.html', error=error, articles=articles, summary=summary, stock_symbol=stock_symbol, nl_summary=nl_summary)

@app.route('/stock', methods=['POST'])
def stock():
    stock_symbol = request.form['stock_symbol'].upper().strip()
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*10)
    try:
        data = yf.download(stock_symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        if data.empty:
            raise ValueError("No data found for this symbol.")
        plt.figure(figsize=(10, 5))
        plt.plot(data['Close'], color='#0033a0')
        plt.title(f'Historical Stock Prices for {stock_symbol} (10 Years)')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.grid(True, color='#d72631', linestyle='--', linewidth=0.5)
        graph_filename = f'{stock_symbol}_graph.png'
        graph_path = os.path.join('static', graph_filename)
        plt.tight_layout()
        plt.savefig(graph_path)
        plt.close()
        # Fetch news articles
        news_articles = get_stock_news(stock_symbol)
        return render_template(
            'stock.html',
            stock_symbol=stock_symbol,
            graph_filename=graph_filename,
            news_articles=news_articles
        )
    except Exception as e:
        error = f"Error: {str(e)}"
        return render_template('index.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)