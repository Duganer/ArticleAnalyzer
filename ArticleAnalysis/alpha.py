# requirements: flask, transformers, requests, beautifulsoup4, datefinder
from ArticleAnalysis import app
from flask import request, jsonify
from transformers import pipeline
from collections import Counter, defaultdict
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from urllib.parse import urlparse
import re

# Initialize the summarization pipeline
summarizer = pipeline("summarization")
sentiment_analyzer = pipeline("sentiment-analysis")

def get_text_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return ' '.join([p.get_text() for p in soup.find_all('p')])

def summarize_text(text, summary_type):
    if summary_type == "one-page synopsis":
        max_length = 600
        min_length = 200
    elif summary_type == "one paragraph synopsis":
        max_length = 150
        min_length = 50
    elif summary_type == "headline":
        max_length = 40
        min_length = 10
    else:
        return None

    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']

def analyze_keywords(text, keywords):
    words = text.lower().split()
    counter = Counter(words)
    return sum(counter[key.lower()] for key in keywords)

def get_article_weight(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    domain_extension = domain.split(".")[-1]

    if domain_extension == "gov":
        return 4.0
    elif domain_extension == "edu":
        return 3.0
    elif domain_extension == "org":
        return 2.0
    elif domain_extension == "com":
        return 1.0
    else:
        return 0.0

def get_article_date(url):


    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content of the page using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    page_body = soup.find('body')
    clean_body = ''.join(str(page_body).replace('\n', ''))
    date_regex = r"([A-Z][a-z]{2,8}|[A-Z]{3})\s(\d{1,2}),\s(\d{4})"
    find_date = get_date_from_text(clean_body)
    if find_date:
        return find_date
    else:
        page_header = soup.find('header')
        clean_header = ''.join(str(page_header).replace('\n', ''))
        find_date = get_date_from_text(clean_header)
        if find_date:
            return find_date

    # If the date is not found, return None
    return None

def get_date_from_text(text):
    date_regex = r"([A-Z][a-z]{2,8}|[A-Z]{3})\s(\d{1,2}),\s(\d{4})"
    match = re.search(date_regex, text, re.IGNORECASE)
    if match:
        month_str, year_str = match.group(1), match.group(3)
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        if len(month_str) > 3:
            month_num = month_map[month_str[:3]]
        else:
            month_num = month_map[month_str]
        return f"{year_str}-{month_num}"
    else:
        return None

def get_sentiment_weight(text):
    sentiment = sentiment_analyzer(text)[0]
    if sentiment['label'] == 'POSITIVE':
        return 10.0
    elif sentiment['label'] == 'NEGATIVE':
        return 1.0
    else:
        return 5.0

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    urls = data.get('urls', [])
    summary_type = data.get('summary_type', 'headline')
    keywords = data.get('keywords', [])

    summaries = []

    for url in urls:
        text = get_text_from_url(url)
        summary = summarize_text(text, summary_type)
        if summary:
            score = analyze_keywords(summary, keywords)
            weight = get_article_weight(url)
            sentiment_weight = get_sentiment_weight(summary)
            weighted_score = score * weight * sentiment_weight
            date = get_article_date(url)
            summaries.append({
                "url": url, 
                "summary": summary, 
                "score": round(score, 2), 
                "weight": round(weight, 2), 
                "sentiment_weight": round(sentiment_weight, 2), 
                "weighted_score": round(weighted_score, 2), 
                "date": date
            })
        else:
            return jsonify({"error": "Invalid summary type provided"}), 400
        
    # Group articles by date
    grouped_articles = defaultdict(list)
    for summary in summaries:
        date = summary["date"]
        if date:
            grouped_articles[date].append(summary)

    # Combine weights for articles published in the same month and year
    combined_weights = {}
    for date, articles in grouped_articles.items():
        combined_weights[date] = sum(article["weighted_score"] for article in articles)

    return jsonify({"results": summaries, "grouped_summaries": combined_weights})
   
@app.route('/summarize_by_date', methods=['POST'])
def summarize_by_date():
    data = request.json
    start_date = data.get('start_date', None)
    end_date = data.get('end_date', None)
    keywords = data.get('keywords', [])
    summary_type = data.get('summary_type', 'headline')

    if not start_date or not end_date:
        return jsonify({"error": "Both start_date and end_date must be provided"}), 400

    date_range = f"{start_date}..{end_date}"
    query = " ".join(keywords) + f" daterange:{date_range}"

    # Search for articles using the googlesearch library
    urls = []
    for url in search(query, num_results=50, lang="en"):
        urls.append(url)

    summaries = []

    for url in urls:
        text = get_text_from_url(url)
        summary = summarize_text(text, summary_type)
        if summary:
            score = analyze_keywords(summary, keywords)
            weight = get_article_weight(url)
            sentiment_weight = get_sentiment_weight(summary)
            weighted_score = score * weight * sentiment_weight
            date = get_article_date(url)
            summaries.append({
                "url": url, 
                "summary": summary, 
                "score": round(score, 2), 
                "weight": round(weight, 2), 
                "sentiment_weight": round(sentiment_weight, 2), 
                "weighted_score": round(weighted_score, 2), 
                "date": date
            })

    # Group articles by date
    grouped_articles = defaultdict(list)
    for summary in summaries:
        date = summary["date"]
        if date:
            grouped_articles[date].append(summary)

    # Combine weights for articles published in the same month and year
    combined_weights = {}
    for date, articles in grouped_articles.items():
        combined_weights[date] = sum(article["weighted_score"] for article in articles)

    return jsonify({"results": summaries, "grouped_summaries": combined_weights})

