from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import yfinance as yf
import requests
from helpers import junior_ai_analyst_recommendation, get_regression_series, dcf_fair_value_estimate, calculate_linear_regression, calculate_dcf_valuation
from sklearn.linear_model import LinearRegression
import numpy as np
import math

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
        # print("News articles:", articles)
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
        data = yf.download(
            stock_symbol,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            auto_adjust=True  # Explicitly set this
        )
        if data.empty:
            raise ValueError("No data found for this symbol.")

        # Regression calculation
        dates = np.array([i for i in range(len(data))]).reshape(-1, 1)
        prices = data['Close'].values.reshape(-1, 1)
        model = LinearRegression()
        model.fit(dates, prices)
        predicted = model.predict(dates)
        predicted_price = calculate_linear_regression(data)

        plt.figure(figsize=(10, 5))
        plt.plot(data.index, data['Close'], label="Actual Price", color='#0033a0')
        plt.plot(data.index, predicted, label="Linear Trend", linestyle='--', color='orange')
        plt.title(f'Historical Stock Prices for {stock_symbol} (10 Years)')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.grid(True, color='#d72631', linestyle='--', linewidth=0.5)
        plt.legend()
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
                close_val = float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close'])
                if close_val is not None:
                    chart_data.append([timestamp, close_val])
            except Exception:
                continue
        regression_data = get_regression_series(data)
        dcf_value = dcf_fair_value_estimate(data)
        current_price = None
        valuation_message = None
        try:
            ticker = yf.Ticker(stock_symbol)
            info = ticker.info
            current_price = info.get("regularMarketPrice", None)
            # Ensure both are floats and not NaN
            try:
                if hasattr(current_price, "item"):
                    current_price = float(current_price.item())
                if hasattr(dcf_value, "item"):
                    dcf_value = float(dcf_value.item())
            except Exception:
                pass

            if (
                dcf_value is not None and
                current_price is not None and
                not math.isnan(dcf_value) and
                not math.isnan(current_price)
            ):
                diff = dcf_value - current_price
                pct = (diff / current_price) * 100
                if diff > 0:
                    valuation_message = f"This stock is <strong style='color:green;'>undervalued</strong> by ${diff:.2f} ({pct:.2f}%)."
                else:
                    valuation_message = f"This stock is <strong style='color:red;'>overvalued</strong> by ${-diff:.2f} ({-pct:.2f}%)."
            else:
                valuation_message = "DCF fair value estimate not available."
        except Exception as e:
            print("Error fetching ticker info:", e)
            valuation_message = "DCF fair value estimate not available."
        return templates.TemplateResponse(
            "stock.html",
            {
                "request": request,
                "stock_symbol": stock_symbol,
                "graph_filename": graph_filename,
                "news_articles": news_articles,
                "nl_summary": nl_summary,
                "chart_data": chart_data,
                "regression_data": regression_data,
                "dcf_value": dcf_value,
                "current_price": current_price,
                "valuation_message": valuation_message,
                "predicted_price": predicted_price,
            }
        )
    except Exception as e:
        error = f"Error: {str(e)}"
        return templates.TemplateResponse("index.html", {"request": request, "error": error})

@app.post("/report", response_class=HTMLResponse)
async def report(request: Request, stock_symbol: str = Form(...)):
    try:
        stock_symbol = stock_symbol.upper().strip()
        ticker = yf.Ticker(stock_symbol)
        info = ticker.info
        hist = ticker.history(period="1y")
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
        # Prepare chart data
        chart_data = []
        for date, row in hist.iterrows():
            try:
                timestamp = int(date.timestamp() * 1000)
                close_val = float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close'])
                if close_val is not None:
                    chart_data.append([timestamp, close_val])
            except Exception:
                continue
        ai_recommendation = junior_ai_analyst_recommendation(
            hist,
            info.get("trailingPE"),
            info.get("epsTrailingTwelveMonths"),
            info.get("averageAnalystRating", ""),
            info.get("dividendYield")
        )
        try:
            from helpers import generate_analyst_reasoning
        except ImportError:
            import importlib.util
            import sys
            helpers_path = os.path.join(os.path.dirname(__file__), 'helpers.py')
            spec = importlib.util.spec_from_file_location('helpers', helpers_path)
            helpers = importlib.util.module_from_spec(spec)
            sys.modules['helpers'] = helpers
            spec.loader.exec_module(helpers)
            generate_analyst_reasoning = helpers.generate_analyst_reasoning
        # Calculate one year return for reasoning
        one_year_return = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0]) * 100
        reasoning_blurb = generate_analyst_reasoning(
            stock_symbol,
            {
                "one_year_return": one_year_return,  # calculate from hist
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("epsTrailingTwelveMonths"),
                "dividend_yield": info.get("dividendYield"),
                "analyst_rating": info.get("averageAnalystRating", ""),
            },
            nl_summary
        )
        current_price = info.get("regularMarketPrice", None)
        dcf_value = calculate_dcf_valuation(info)

        # Ensure both are floats and not NaN
        try:
            if hasattr(current_price, "item"):
                current_price = float(current_price.item())
            if hasattr(dcf_value, "item"):
                dcf_value = float(dcf_value.item())
        except Exception:
            pass

        if (
            dcf_value is not None and
            current_price is not None and
            not math.isnan(dcf_value) and
            not math.isnan(current_price)
        ):
            diff = dcf_value - current_price
            pct = (diff / current_price) * 100
            if diff > 0:
                valuation_message = f"This stock is <strong style='color:green;'>undervalued</strong> by ${diff:.2f} ({pct:.2f}%)."
            else:
                valuation_message = f"This stock is <strong style='color:red;'>overvalued</strong> by ${-diff:.2f} ({-pct:.2f}%)."
        else:
            valuation_message = "DCF fair value estimate not available."

        print("YFinance info for", stock_symbol, ":", info)  # <-- Add this line
        return templates.TemplateResponse(
            "report.html",
            {
                "request": request,
                "stock_symbol": stock_symbol,
                "company_name": info.get("shortName", ""),
                "current_price": info.get("regularMarketPrice", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "week_low": info.get("fiftyTwoWeekLow", "N/A"),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", ""),
                "analyst_rating": info.get("averageAnalystRating", info.get("recommendationKey", "N/A")),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "eps": info.get("epsTrailingTwelveMonths", "N/A"),
                "beta": info.get("beta", "N/A"),
                "volume": info.get("regularMarketVolume", "N/A"),
                "target_price": info.get("targetMeanPrice", "N/A"),
                "logo_url": info.get("logo_url", ""),
                "chart_data": chart_data,
                "news_articles": news_articles,
                "nl_summary": nl_summary,
                "ai_recommendation": ai_recommendation,
                "reasoning_blurb": reasoning_blurb,
                "valuation_message": valuation_message,
            }
        )
    except Exception as e:
        error = f"Error: {str(e)}"
        return templates.TemplateResponse("index.html", {"request": request, "error": error})

def simple_dcf_valuation(ticker, years=5, discount_rate=0.10, perpetual_growth=0.02):
    """
    Returns estimated fair value per share using a conservative DCF model.
    """
    import numpy as np
    import yfinance as yf

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

        if op_cash_row is not None and capex_row is not None and cashflow.shape[1] > 0:
            op_cash = cashflow.loc[op_cash_row][0]
            capex = cashflow.loc[capex_row][0]
            if not np.isnan(op_cash) and not np.isnan(capex):
                fcf = float(op_cash) - float(capex)
            else:
                raise ValueError("NaN in cashflow rows")
        else:
            raise ValueError("Missing required cashflow rows")
    except Exception as e:
        print(f"Exception in DCF cashflow for {ticker}: {e}")
        # Fallback to freeCashflow or a conservative EPS proxy
        try:
            info = stock.info
            shares_outstanding = info.get('sharesOutstanding', 0)
            if not shares_outstanding:
                return None
            fcf = info.get('freeCashflow')
            if fcf is not None:
                fcf = float(fcf)
            else:
                eps = info.get('trailingEps')
                if not eps:
                    return None
                fcf = eps * 0.15 * shares_outstanding  # Very conservative proxy
        except Exception as e2:
            print(f"Exception in DCF fallback for {ticker}: {e2}")
            return None

    # Conservative assumptions
    fcf_growth = 0.03
    projected_fcfs = [fcf * ((1 + fcf_growth) ** i) for i in range(1, years + 1)]
    discounted_fcfs = [fcf_ / ((1 + discount_rate) ** i) for i, fcf_ in enumerate(projected_fcfs, 1)]
    terminal_value = projected_fcfs[-1] * (1 + perpetual_growth) / (discount_rate - perpetual_growth)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** years)
    dcf_value = sum(discounted_fcfs) + discounted_terminal

    try:
        shares_outstanding = stock.info.get('sharesOutstanding', None)
        if not shares_outstanding or shares_outstanding == 0:
            print(f"Shares outstanding missing or zero for {ticker}: {shares_outstanding}")
            return None
    except Exception as e:
        print(f"Exception in DCF shares outstanding for {ticker}: {e}")
        return None

    fair_value_per_share = dcf_value / shares_outstanding
    print(f"DCF fair value for {ticker}: {fair_value_per_share}")
    return round(fair_value_per_share, 2)

