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
        f"q={stock_symbol} stock news&"
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
        try:
            from helpers import generate_natural_language_summary
        except ImportError:
            import importlib.util
            import sys
            helpers_path = os.path.join(os.path.dirname(__file__), 'helpers.py')
            spec = importlib.util.spec_from_file_location('helpers', helpers_path)
            helpers = importlib.util.module_from_spec(spec)
            sys.modules['helpers'] = helpers
            spec.loader.exec_module(helpers)
            generate_natural_language_summary = helpers.generate_natural_language_summary
        nl_summary = generate_natural_language_summary(news_articles, stock_symbol) if news_articles else None
        # Prepare data for Highcharts: list of [timestamp, close]
        chart_data = []
        for date, row in data.iterrows():
            try:
                timestamp = int(date.timestamp() * 1000)
                close_val = float(row['Close'])
                if close_val is not None:
                    chart_data.append([timestamp, close_val])
            except Exception:
                continue
        return render_template(
            'stock.html',
            stock_symbol=stock_symbol,
            graph_filename=graph_filename,
            news_articles=news_articles,
            nl_summary=nl_summary,
            chart_data=chart_data
        )
    except Exception as e:
        error = f"Error: {str(e)}"
        return render_template('index.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)