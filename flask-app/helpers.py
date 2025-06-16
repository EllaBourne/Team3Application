from transformers import pipeline
import numpy as np
from sklearn.linear_model import LinearRegression

# Load once at module level
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def generate_natural_language_summary(articles, ticker=None):
    texts = []
    for a in articles[:8]:
        content = a.get("content", "")
        if "[+" in content:
            content = content.split("[+")[0].strip()
        parts = [a.get("title", ""), a.get("description", ""), content]
        texts.append(" ".join([p for p in parts if p]))
    cleaned = " ".join(texts).strip()
    if not cleaned:
        return "No summary available."
    cleaned = cleaned[:1500]

    prompt = (
        f"You are a senior financial analyst. Your task is to summarize the following recent news about {ticker or 'the stock'} for investors.\n\n"
        "Focus only on the news content below. Do not include financial ratios, price data, or company fundamentals unless they are mentioned in the news itself.\n"
        "Write a concise, 2-3 sentence summary that highlights the most important developments, risks, or opportunities for investors.\n"
        "Do not list headlines or repeat text verbatim. Synthesize the news into clear, actionable insights.\n\n"
        f"=== BEGIN NEWS ===\n{cleaned}\n=== END NEWS ==="
    )

    input_length = len(cleaned.split())
    max_length = min(100, input_length + 10)
    summary = summarizer(
        prompt,
        max_length=max_length,
        min_length=10,
        do_sample=False,
        num_beams=4,
        no_repeat_ngram_size=3,
        repetition_penalty=1.2,
    )
    return summary[0]['summary_text']

def junior_ai_analyst_recommendation(hist, pe_ratio, eps, analyst_rating, dividend_yield):
    closes = np.array([row['Close'] for _, row in hist.iterrows()])
    if len(closes) < 2:
        return "Not enough data for AI recommendation."
    one_year_return = (closes[-1] - closes[0]) / closes[0]

    score = 0
    if one_year_return > 0.10: score += 1
    if pe_ratio and pe_ratio < 25: score += 1
    if eps and eps > 0: score += 1
    if analyst_rating and "buy" in analyst_rating.lower(): score += 1
    if dividend_yield and dividend_yield > 0.01: score += 1

    if score >= 4:
        return "Junior AI Analyst: Strong Buy (based on positive price trend, healthy fundamentals, and favorable analyst outlook)."
    elif score == 3:
        return "Junior AI Analyst: Buy (good overall, but some caution advised)."
    elif score == 2:
        return "Junior AI Analyst: Hold (mixed signals, further review recommended)."
    else:
        return "Junior AI Analyst: Sell or Avoid (weak trend or fundamentals)."

def generate_analyst_reasoning(ticker, stats, news_summary):
    prompt = (
        f"You are a junior quantitative analyst reviewing the stock report for {ticker}.\n\n"
        "Given the following key statistics, use data-driven reasoning to explain in 2-3 sentences the main factors behind your investment recommendation. "
        "Reference quantitative metrics such as 1-year return, P/E ratio, EPS, dividend yield, and analyst rating. "
        "Avoid generic statements; focus on statistical signals and model-based insights.\n"
        f"- 1-year return: {stats.get('one_year_return', 'N/A')}\n"
        f"- P/E ratio: {stats.get('pe_ratio', 'N/A')}\n"
        f"- EPS: {stats.get('eps', 'N/A')}\n"
        f"- Dividend yield: {stats.get('dividend_yield', 'N/A')}\n"
        f"- Analyst rating: {stats.get('analyst_rating', 'N/A')}\n\n"
        "Write your reasoning in clear, natural language for investors."
    )
    summary = summarizer(prompt, max_length=100, min_length=40, do_sample=False, num_beams=4, no_repeat_ngram_size=3, repetition_penalty=1.2)
    return summary[0]['summary_text']

def get_regression_series(data):
    dates = np.array([i for i in range(len(data))]).reshape(-1, 1)
    prices = data['Close'].values.reshape(-1, 1)
    model = LinearRegression()
    model.fit(dates, prices)
    predicted = model.predict(dates)
    regression_series = [[int(data.index[i].timestamp() * 1000), float(predicted[i])] for i in range(len(data))]
    return regression_series

def calculate_linear_regression(data):
    dates = np.array([i for i in range(len(data))]).reshape(-1, 1)
    prices = data['Close'].values.reshape(-1, 1)
    model = LinearRegression()
    model.fit(dates, prices)
    next_day = np.array([[len(data)]])
    predicted_price = model.predict(next_day)
    return round(predicted_price[0][0], 2)

def dcf_fair_value_estimate(data):
    fcf = data['Close'].mean() * 0.2  # Simulated FCF
    growth_rate = 0.08
    discount_rate = 0.10
    years = 5
    discounted_fcfs = [fcf * ((1 + growth_rate) ** t) / ((1 + discount_rate) ** t) for t in range(1, years + 1)]
    terminal_value = (fcf * (1 + growth_rate)) / (discount_rate - growth_rate)
    discounted_terminal = terminal_value / ((1 + discount_rate) ** years)
    return round(sum(discounted_fcfs) + discounted_terminal, 2)

def calculate_dcf_valuation(info, years=5, discount_rate=0.10, perpetual_growth=0.02):
    """
    Returns estimated fair value per share using a DCF model based on actual cash flows.
    Falls back to a conservative EPS proxy if needed.
    """
    import numpy as np
    import yfinance as yf

    try:
        ticker = info.get("symbol") or info.get("shortName", "")
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow

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
            raise ValueError("Missing required cashflow rows")

        op_cash = cashflow.loc[op_cash_row][0]
        capex = cashflow.loc[capex_row][0]

        if np.isnan(op_cash) or np.isnan(capex):
            raise ValueError("NaN in cashflow rows")

        fcf = float(op_cash) - float(capex)

        # Conservative growth assumptions
        fcf_growth = 0.03
        projected_fcfs = [fcf * ((1 + fcf_growth) ** i) for i in range(1, years + 1)]
        discounted_fcfs = [fcf_ / ((1 + discount_rate) ** i) for i, fcf_ in enumerate(projected_fcfs, 1)]
        terminal_value = projected_fcfs[-1] * (1 + perpetual_growth) / (discount_rate - perpetual_growth)
        discounted_terminal = terminal_value / ((1 + discount_rate) ** years)
        dcf_value = sum(discounted_fcfs) + discounted_terminal

        shares_outstanding = info.get("sharesOutstanding", None)
        if not shares_outstanding or shares_outstanding == 0:
            raise ValueError("Missing or zero shares outstanding")

        fair_value_per_share = dcf_value / shares_outstanding
        return round(fair_value_per_share, 2)
    except Exception as e:
        print("DCF fallback due to error:", e)
        # Fallback to conservative proxy if cashflow data is missing
        try:
            shares_outstanding = info.get("sharesOutstanding", 0)
            if not shares_outstanding:
                return None

            fcf = info.get("freeCashflow")
            if fcf is not None:
                fcf = float(fcf)
            else:
                eps = info.get("trailingEps")
                if not eps:
                    return None
                fcf = eps * 0.15 * shares_outstanding  # Very conservative proxy

            growth_rate = 0.02
            terminal_growth = 0.01

            projected_fcfs = [fcf * (1 + growth_rate) ** i for i in range(1, years + 1)]
            terminal_value = projected_fcfs[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
            discounted_fcfs = [fcf_ / ((1 + discount_rate) ** (i + 1)) for i, fcf_ in enumerate(projected_fcfs)]
            discounted_terminal = terminal_value / ((1 + discount_rate) ** years)
            enterprise_value = sum(discounted_fcfs) + discounted_terminal
            fair_value_per_share = enterprise_value / shares_outstanding
            return round(fair_value_per_share, 2)
        except Exception as e2:
            print("DCF error (fallback also failed):", e2)
            return None

