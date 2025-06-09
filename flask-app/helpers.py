from transformers import PegasusTokenizer, PegasusForConditionalGeneration, pipeline

model_name = "human-centered-summarization/financial-summarization-pegasus"
tokenizer = PegasusTokenizer.from_pretrained(model_name)
model = PegasusForConditionalGeneration.from_pretrained(model_name)

summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

def generate_natural_language_summary(articles, ticker=None):
    texts = [a.get("description") or a.get("title") or "" for a in articles[:5]]
    cleaned = " ".join(texts).strip()
    if not cleaned:
        return "No summary available."

    cleaned = cleaned[:1000]

    prompt = (
        f"You are a senior financial analyst reviewing the latest news about {ticker if ticker else 'the stock'}.\n\n"
        "Analyze the developments using the following chain of reasoning:\n"
        "1. What are the main facts reported?\n"
        "2. What are the implications for investors or the market?\n"
        "3. What risks or opportunities can be inferred?\n\n"
        "Then, write a 3-sentence, polished summary suitable for an investor briefing. "
        "Avoid listing headlines directly — instead, synthesize insights into natural language.\n\n"
        f"Don't include irrelevant details about random stocks unless you can tie it back to {ticker if ticker else 'the stock'}.\n\n"
        "News:\n"
        + cleaned
    )

    summary = summarizer(
        prompt,
        max_length=100,
        min_length=40,
        do_sample=False,
        num_beams=4,
        no_repeat_ngram_size=3,
        repetition_penalty=1.2,
    )

    return summary[0]['summary_text']
