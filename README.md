# reddit-prediction-scanner

A beginner-friendly Python project that uses Reddit's official API through PRAW to scan finance-related subreddits for public prediction-like statements.

This tool saves candidate predictions to a local SQLite database and exports them to CSV for manual review.

It is not a trading tool, not a gambling tool, and not financial advice.

## What it scans

By default, `scanner.py` scans recent posts and top-level comments from:

- `r/stocks`
- `r/investing`
- `r/wallstreetbets`
- `r/options`
- `r/StockMarket`

It looks for phrases such as:

- `will hit`
- `will reach`
- `going to hit`
- `above $`
- `below $`
- `by end of year`
- `by 2026`
- `price target`
- `earnings beat`
- `earnings miss`

The scanner tries to extract a ticker, target price, rough deadline, and confidence percentage. If extraction is uncertain, those fields are left blank and the row is still saved for human review.

## Project files

- `requirements.txt` lists the Python packages to install.
- `.env.example` shows the Reddit API credential variables you need.
- `database.py` creates and writes to the SQLite database.
- `scanner.py` scans Reddit and saves candidate predictions.
- `export_csv.py` exports database rows to `predictions_export.csv`.
- `README.md` explains setup and usage.

## Create a Reddit API app

1. Log in to Reddit.
2. Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).
3. Click **create app** or **create another app**.
4. Choose **script** as the app type.
5. Give it a name, such as `reddit-prediction-scanner`.
6. Use `http://localhost:8080` as the redirect URI. This project does not use the redirect, but Reddit requires one.
7. After creating the app, copy:
   - the client ID shown under the app name
   - the client secret

## Configure credentials

Copy `.env.example` to a new file named `.env`:

```bash
cp .env.example .env
```

On Windows PowerShell, you can use:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=reddit-prediction-scanner/0.1 by your_reddit_username
```

Use a descriptive user agent that includes your Reddit username.

## Install requirements

Create and activate a virtual environment if you want to keep dependencies isolated:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Run the scanner

```bash
python scanner.py
```

The scanner creates a local SQLite database named `predictions.db` and a table named `predictions`.

Duplicate entries are avoided with the `post_or_comment_id` column, so running the scanner multiple times should not insert the same Reddit post or comment again.

## Export to CSV

After running the scanner, export all database rows:

```bash
python export_csv.py
```

This creates:

```text
predictions_export.csv
```

## Database columns

The `predictions` table contains:

- `id`
- `source_platform`
- `subreddit`
- `author`
- `post_or_comment_id`
- `prediction_text`
- `full_text`
- `asset`
- `target_value`
- `deadline`
- `confidence`
- `created_utc`
- `source_url`
- `status`
- `notes`

## Important warnings

- This project uses Reddit's official API through PRAW.
- Do not scrape Reddit HTML.
- Respect Reddit's API rules, rate limits, user privacy, and subreddit rules.
- This tool only collects public prediction-like statements for research and manual review.
- Do not use this project to make investment decisions.
- Nothing in this project is financial advice.
