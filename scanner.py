"""Scan Reddit for finance-related prediction-like statements.

This script uses Reddit's official API through PRAW. It does not scrape Reddit
HTML pages. The goal is to collect public candidate predictions for manual
research/review, not to make investment recommendations.
"""

import os
import re

import praw
from dotenv import load_dotenv

from database import initialize_database, save_prediction


DEFAULT_SUBREDDITS = [
    "stocks",
    "investing",
    "wallstreetbets",
    "options",
    "StockMarket",
]

PREDICTION_PHRASES = [
    "will hit",
    "will reach",
    "going to hit",
    "above $",
    "below $",
    "by end of year",
    "by 2026",
    "price target",
    "earnings beat",
    "earnings miss",
]

# A small list of common market words that look like tickers but usually are not.
COMMON_FALSE_TICKERS = {
    "A",
    "AI",
    "ATH",
    "CEO",
    "CFO",
    "DD",
    "EPS",
    "ETF",
    "GDP",
    "IPO",
    "ITM",
    "OTM",
    "PE",
    "SEC",
    "USA",
    "USD",
}


def create_reddit_client():
    """Create a read-only Reddit API client from environment variables."""
    load_dotenv()

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not client_id or not client_secret or not user_agent:
        raise RuntimeError(
            "Missing Reddit API credentials. Copy .env.example to .env and fill "
            "in REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def contains_prediction_phrase(text):
    """Return True if the text contains one of our prediction-like phrases."""
    lower_text = text.lower()
    return any(phrase in lower_text for phrase in PREDICTION_PHRASES)


def extract_ticker(text):
    """Try to extract a stock ticker symbol.

    This intentionally uses simple rules. It catches common forms like "$AAPL"
    and "AAPL", but it will not be perfect. Uncertain results are fine because
    every row is meant for human review.
    """
    cashtag_match = re.search(r"\$([A-Z]{1,5})(?![A-Za-z])", text)
    if cashtag_match:
        return cashtag_match.group(1)

    uppercase_matches = re.findall(r"\b[A-Z]{2,5}\b", text)
    for match in uppercase_matches:
        if match not in COMMON_FALSE_TICKERS:
            return match

    return ""


def extract_target_value(text):
    """Try to extract a target price/value such as '$250' or '$1,200.50'."""
    money_match = re.search(r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)", text)
    if money_match:
        return money_match.group(1).replace(",", "")

    return ""


def extract_deadline(text):
    """Try to extract a rough deadline phrase."""
    deadline_patterns = [
        r"by end of year",
        r"by eoy",
        r"by q[1-4]\s?20[0-9]{2}",
        r"by q[1-4]",
        r"by 20[0-9]{2}",
        r"by (?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s?20?[0-9]{2}",
        r"next (?:week|month|quarter|year)",
    ]

    for pattern in deadline_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)

    return ""


def extract_confidence(text):
    """Try to extract a confidence percentage, such as '80%'."""
    confidence_match = re.search(r"\b([1-9][0-9]?|100)\s?%", text)
    if confidence_match:
        return f"{confidence_match.group(1)}%"

    return ""


def shorten_prediction_text(text, max_length=300):
    """Keep a readable snippet for the prediction_text field."""
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3] + "..."


def build_prediction_record(item, subreddit_name, full_text):
    """Convert a Reddit post/comment into a database-ready dictionary."""
    permalink = getattr(item, "permalink", "")
    author = getattr(item, "author", None)

    return {
        "source_platform": "reddit",
        "subreddit": subreddit_name,
        "author": str(author) if author else "[deleted]",
        "post_or_comment_id": item.id,
        "prediction_text": shorten_prediction_text(full_text),
        "full_text": full_text,
        "asset": extract_ticker(full_text),
        "target_value": extract_target_value(full_text),
        "deadline": extract_deadline(full_text),
        "confidence": extract_confidence(full_text),
        "created_utc": getattr(item, "created_utc", None),
        "source_url": f"https://www.reddit.com{permalink}" if permalink else "",
        "status": "needs_review",
        "notes": "Automatically collected candidate. Review manually before use.",
    }


def scan_submission(submission, subreddit_name, comment_limit):
    """Yield candidate predictions from one post and its top-level comments."""
    post_text = f"{submission.title}\n{submission.selftext or ''}".strip()
    if contains_prediction_phrase(post_text):
        yield build_prediction_record(submission, subreddit_name, post_text)

    # PRAW can fetch many nested comments. Setting replace_more(limit=0) avoids
    # extra pagination and keeps this beginner project gentle on API usage.
    submission.comments.replace_more(limit=0)

    for comment in submission.comments[:comment_limit]:
        comment_text = getattr(comment, "body", "")
        if contains_prediction_phrase(comment_text):
            yield build_prediction_record(comment, subreddit_name, comment_text)


def scan_subreddits(post_limit=25, comment_limit=10):
    """Scan default subreddits and save candidate predictions."""
    initialize_database()
    reddit = create_reddit_client()

    total_saved = 0
    total_seen = 0

    for subreddit_name in DEFAULT_SUBREDDITS:
        print(f"Scanning r/{subreddit_name}...")
        subreddit = reddit.subreddit(subreddit_name)

        for submission in subreddit.new(limit=post_limit):
            for prediction in scan_submission(submission, subreddit_name, comment_limit):
                total_seen += 1
                total_saved += save_prediction(prediction)

    print(f"Found {total_seen} candidate predictions.")
    print(f"Saved {total_saved} new rows to predictions.db.")
    print("Duplicate Reddit posts/comments are ignored automatically.")


if __name__ == "__main__":
    scan_subreddits()
