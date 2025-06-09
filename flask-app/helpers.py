from transformers import pipeline

# Use a fast, open summarization model for local inference
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def validate_ticker(ticker):
    if not ticker or not ticker.isalnum() or len(ticker) > 8:
        return False
    return True

def format_sentiment_summary(sentiment_counts):
    return f"{sentiment_counts['Positive']} Positive, {sentiment_counts['Neutral']} Neutral, {sentiment_counts['Negative']} Negative"

def generate_natural_language_summary(articles):
    texts = [a.get('title', '') + '. ' + (a.get('description', '') or '') for a in articles if a.get('description') or a.get('title')]
    if not texts:
        return "No summary available."
    joined = " ".join(texts)
    joined = joined[:1200]  # Shorter input for speed
    # Use a unique prompt to guide the summarizer for a more analytical, insightful summary
    prompt = (
        "You are a financial analyst. Read the following recent news headlines and descriptions about a stock. "
        "Write a concise, 3-4 sentence expert summary that synthesizes the main events, trends, and implications for investors. "
        "Highlight any emerging themes, risks, or opportunities, and avoid simply repeating the headlines. "
        "Here is the news: " + joined
    )
    # Generate a shorter summary (about 3-4 sentences)
    summary = summarizer(prompt, max_length=80, min_length=40, do_sample=False)[0]['summary_text']
    return summary