from transformers import pipeline
import numpy as np

# Load once at the top of your helpers.py
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

result = summarizer("Apple stock rose today after strong earnings.", max_length=50, min_length=10, do_sample=False)
print(result[0]['summary_text'])

def generate_natural_language_summary(articles, ticker=None):
    texts = []
    for a in articles[:8]:  # Use more articles if available
        # Clean up content field
        content = a.get("content", "")
        if "[+" in content:
            content = content.split("[+")[0].strip()
        parts = [a.get("title", ""), a.get("description", ""), content]
        texts.append(" ".join([p for p in parts if p]))
    cleaned = " ".join(texts).strip()
    if not cleaned:
        return "No summary available."
    cleaned = cleaned[:1500]  # Truncate if needed

    prompt = (
        f"You are a senior financial analyst. Your task is to summarize the following recent news about {ticker or 'the stock'} for investors.\n\n"
        "Focus only on the news content below. Do not include financial ratios, price data, or company fundamentals unless they are mentioned in the news itself.\n"
        "Write a concise, 2-3 sentence summary that highlights the most important developments, risks, or opportunities for investors.\n"
        "Do not list headlines or repeat text verbatim. Synthesize the news into clear, actionable insights.\n\n"
        "=== BEGIN NEWS ===\n"
        f"{cleaned}\n"
        "=== END NEWS ==="
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
    # Calculate 1-year return
    closes = np.array([row['Close'] for _, row in hist.iterrows()])
    if len(closes) < 2:
        return "Not enough data for AI recommendation."
    one_year_return = (closes[-1] - closes[0]) / closes[0]
    # Simple logic: combine return, P/E, EPS, analyst rating, dividend
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
    """
    stats: dict with keys like 'pe_ratio', 'eps', 'dividend_yield', 'one_year_return', 'analyst_rating'
    news_summary: string, the output from your news summarizer
    """
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
    print("Prompt:", prompt)
    summary = summarizer(prompt, max_length=100, min_length=40, do_sample=False, num_beams=4, no_repeat_ngram_size=3, repetition_penalty=1.2)
    print("Summary:", summary)
    return summary[0]['summary_text']
