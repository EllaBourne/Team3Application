import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download('vader_lexicon', quiet=True)


def analyze_articles(articles):
    sia = SentimentIntensityAnalyzer()
    sentiment_counts = {'Positive': 0, 'Neutral': 0, 'Negative': 0}
    analyzed = []
    for article in articles:
        desc = article.get('description') or ''
        title = article.get('title') or ''
        text = f"{title}. {desc}"
        score = sia.polarity_scores(text)
        compound = score['compound']
        if compound >= 0.05:
            sentiment = 'Positive'
            sentiment_counts['Positive'] += 1
        elif compound <= -0.05:
            sentiment = 'Negative'
            sentiment_counts['Negative'] += 1
        else:
            sentiment = 'Neutral'
            sentiment_counts['Neutral'] += 1
        article['sentiment'] = sentiment
        analyzed.append(article)
    return analyzed, sentiment_counts
