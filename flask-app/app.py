from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import yfinance as yf
import requests
from sklearn.linear_model import LinearRegression
import numpy as np

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "error": None})

@app.post("/stock", response_class=HTMLResponse)
async def stock(request: Request, stock_symbol: str = Form(...)):
    stock_symbol = stock_symbol.upper().strip()
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*10)
    try:
        data = yf.download(stock_symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        if data is None or data.empty:
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
        # Prepare data for regression
        data = data.reset_index()
        data['timestamp'] = data['Date'].map(lambda x: x.timestamp())
        X = np.array(data['timestamp'].values).reshape(-1, 1)
        y = np.array(data['Close'].values)

        # Assign higher weights to more recent data
        # Example: linearly increasing weights from 1 (oldest) to 3 (most recent)
        n = len(data)
        sample_weight = np.linspace(1, 3, n)

        # Train linear regression with sample weights
        model = LinearRegression()
        model.fit(X, y, sample_weight=sample_weight)

        # Predict for the next N days (e.g., 180 days)
        future_days = 180
        last_timestamp = X[-1][0]
        one_day = 24 * 60 * 60
        future_timestamps = np.array([last_timestamp + i * one_day for i in range(1, future_days + 1)]).reshape(-1, 1)
        future_preds = model.predict(future_timestamps)

        # Prepare predicted data for Highcharts
        predicted_data = [[int(ts[0] * 1000), float(pred)] for ts, pred in zip(future_timestamps, future_preds)]
        dcf_fair_value = simple_dcf_valuation(stock_symbol)

        latest_close = chart_data[-1][1] if chart_data else None

        if dcf_fair_value and latest_close:
            valuation_diff = dcf_fair_value - latest_close
            valuation_pct = (valuation_diff / latest_close) * 100
            valuation_status = "undervalued" if valuation_diff > 0 else "overvalued"
        else:
            valuation_diff = None
            valuation_pct = None
            valuation_status = None

        return templates.TemplateResponse(
            "stock.html",
            {
                "request": request,
                "stock_symbol": stock_symbol,
                "graph_filename": graph_filename,
                "news_articles": news_articles,
                "nl_summary": nl_summary,
                "chart_data": chart_data,
                "predicted_data": predicted_data,
                "dcf_fair_value": dcf_fair_value,
                "latest_close": latest_close,
                "valuation_diff": valuation_diff,
                "valuation_pct": valuation_pct,
                "valuation_status": valuation_status,
            }
        )
    except Exception as e:
        error = f"Error: {str(e)}"
        return templates.TemplateResponse("index.html", {"request": request, "error": error})

def simple_dcf_valuation(ticker, years=5, discount_rate=0.10, perpetual_growth=0.025):
    """
    Returns estimated fair value per share using a simple DCF model.
    """
    stock = yf.Ticker(ticker)
    try:
        cashflow = stock.cashflow

        # Try both possible row names for operating cash flow
        op_cash_row = None
        for possible in ['Total Cash From Operating Activities', 'Operating Cash Flow']:
            if possible in cashflow.index:
                op_cash_row = possible
                break

        capex_row = None
        for possible in ['Capital Expenditures', 'Capital Expenditure']:
            if possible in cashflow.index:
                capex_row = possible
                break

        if op_cash_row is None or capex_row is None or cashflow.shape[1] == 0:
            print(f"Missing required cashflow rows for {ticker}: {cashflow.index}")
            return None  # Not enough data

        op_cash = cashflow.loc[op_cash_row][0]
        capex = cashflow.loc[capex_row][0]
        if np.isnan(op_cash) or np.isnan(capex):
            print(f"NaN values in cashflow for {ticker}: op_cash={op_cash}, capex={capex}")
            return None  # Missing values

        fcf = float(op_cash) - float(capex)
    except Exception as e:
        print(f"Exception in DCF cashflow for {ticker}: {e}")
        return None  # Not enough data

    # Estimate future FCFs with a simple growth assumption (e.g., 5% per year)
    fcf_growth = 0.05
    projected_fcfs = [fcf * ((1 + fcf_growth) ** i) for i in range(1, years + 1)]

    # Discount future FCFs to present value
    discounted_fcfs = [fcf / ((1 + discount_rate) ** i) for i, fcf in enumerate(projected_fcfs, 1)]

    # Terminal value (Gordon Growth Model)
    terminal_value = projected_fcfs[-1] * (1 + perpetual_growth) / (discount_rate - perpetual_growth)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** years)

    # Enterprise value
    dcf_value = sum(discounted_fcfs) + discounted_terminal

    # Get shares outstanding
    try:
        shares_outstanding = stock.info.get('sharesOutstanding', None)
        if not shares_outstanding or shares_outstanding == 0:
            print(f"Shares outstanding missing or zero for {ticker}: {shares_outstanding}")
            return None
    except Exception as e:
        print(f"Exception in DCF shares outstanding for {ticker}: {e}")
        return None

    # Fair value per share
    fair_value_per_share = dcf_value / shares_outstanding
    print(f"DCF fair value for {ticker}: {fair_value_per_share}")
    return round(fair_value_per_share, 2)

# To run: uvicorn app:app --reload