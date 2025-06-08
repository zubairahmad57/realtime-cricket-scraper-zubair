# Real-Time Cricket Data Scraper

## 🏏 Overview
This project is a real-time web scraper for cricket data from *[crex.live](https://crex.live)*.  
It scrapes:

- Upcoming match list  
- Detailed match info  
- Live score updates  
- Full scorecards  

All data is stored in *MongoDB, and jobs are managed using a **scheduler* to trigger scraping at the right time.

## ⚙️ Technologies Used
- *Selenium* – for dynamic browser interaction  
- *BeautifulSoup4* – for HTML parsing  
- *MongoDB* – for storing match data  
- *APScheduler* – to automate scraping tasks  
- *Python* – main programming language  

## 📅 Scheduler Execution Flow
The scraper automatically triggers jobs each day at specific times:

| Time       | Job                                     |
|------------|------------------------------------------|
| 06:00 AM   | Scrape list of today's matches           |
| 07:00 AM   | Update each match's basic details        |
| 08:00 AM   | Schedule real-time scraping per match    |

Once a match is scheduled:

- ⏲️ 20 mins before match → Scrape match details  
- 🕒 Match start time → Start scraping:
  - Live page data (commentary, status)  
  - Scorecard data (batsmen, bowlers, etc.)

## 🧾 MongoDB Collections
Data is stored in the following collections:
- match_list – upcoming and scheduled matches  
- match_details – teams, venue, toss, etc.  
- scorecard – ball-by-ball info & stats  
- live_page – real-time score & status  

## 🚀 Setup Instructions
1. Clone the repo and set up environment variables:  
   - Copy .env from sample.env and fill required values.

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate     # On Windows: venv\Scripts\activate

3. Install dependencies:

pip install -r requirements.txt



▶️ Start the App

Run the scheduler to begin automated scraping:

python main.py

This will:

Automatically scrape match info and scores

Schedule all required scraping jobs

Store everything into MongoDB


✅ Status

✔️ Code tested on local environment
✔️ All scraping functions are working as expected
✔️ Headless mode used for performance

📌 Note

This project is designed for real-time cricket data scraping.
If you want to test it, make sure ChromeDriver and Chrome versions match and MongoDB is running locally or via URI.

👤 Author

Built with ❤️ by Zubair Ahmad – feel free to fork or raise issues.