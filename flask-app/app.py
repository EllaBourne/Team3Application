from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import yfinance as yf
import requests

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
    return render_template('index.html', error=error)

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