from datetime import datetime, timedelta
import time
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import Scraper
from scraper.get_match_details import get_all_match_details
from scraper.utils import (
    save_to_db,
    db_client,
    db,
    match_details_collection,
    match_list_collection,
    scorecard_collection,
    live_page_collection,
    logger
)

# Thread pool executor with limit
executor = ThreadPoolExecutor(max_workers=5)
scheduler = BackgroundScheduler()

def schedule_jobs():
    global scheduler

    scheduler.add_job(scrape_match_list, 'interval', days=1, start_date=datetime.now() + timedelta(seconds=5))
    scheduler.add_job(get_all_match_details, 'interval', days=1, start_date=datetime.now() + timedelta(seconds=10))
    scheduler.add_job(schedule_timed_jobs_for_today_matches, 'interval', days=1, start_date=datetime.now() + timedelta(seconds=15))

    try:
        print("Scheduler started. Daily jobs are scheduled.")
        scheduler.start()
        while True:
            time.sleep(60)  # Keep main thread alive
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down scheduler.")
        scheduler.shutdown()

def schedule_timed_jobs_for_today_matches():
    """Schedule match-specific jobs for today's matches."""
    today = datetime.now().date()
    today_str = today.strftime("%b %d, %Y")

    logger.info(f"Scheduling jobs for matches on: {today_str}")
    upcoming_matches = match_details_collection.find({"match_date": {"$regex": today_str}})
   
    for match in upcoming_matches:
        try:
            logger.info(f"Scheduling for match: {match['match_date']}")
            match_id = match["match_id"]
            match_link = match["match_link"]
            match_start_time = datetime.strptime(match["match_date"], "%b %d, %Y, %I:%M:%S %p")

            match_20_min_before = match_start_time - timedelta(minutes=20)

            scheduler.add_job(
                match_details_job_wrapper,
                'date',
                run_date=match_20_min_before,
                args=[match_id, match_link]
            )

            scheduler.add_job(
                live_scraping_wrapper,
                'date',
                run_date=match_start_time,
                args=[match_id, match_link]
            )
        except Exception as e:
            logger.error(f"Failed to schedule for match {match.get('match_id')}: {e}")

def match_details_job_wrapper(match_id, match_link):
    executor.submit(scrape_match_details, match_id, match_link)

def live_scraping_wrapper(match_id, match_link):
    executor.submit(start_live_scraping, match_id, match_link)

def scrape_match_list():
    try:
        logger.info("Starting to scrape match list...")
        scraper = Scraper()
        match_list_data = scraper.scrape_match_list()
        save_to_db(match_list_collection, match_list_data, unique_field="link")
        logger.info("Match list scraping completed successfully.")
    except Exception as e:
        logger.error(f"Error occurred while scraping match list: {e}")

def scrape_match_details(match_id, match_link):
    try:
        logger.info(f"Starting to scrape match details for match ID: {match_id}...")
        details_scraper = Scraper(isMonitoring=False)
        match_details = details_scraper.scrape_match_details(match_link)
        match_details_collection.update_one({"match_id": match_id}, {"$set": match_details})
        logger.info(f"Match details for match ID {match_id} scraped and saved successfully.")
    except Exception as e:
        logger.error(f"Error occurred while scraping match details for match ID {match_id}: {e}")

def start_live_scraping(match_id, match_link):
    try:
        logger.info(f"Starting live scraping for match ID: {match_id}...")

        base_url = "https://www.crex.live/"
        match_link_live = base_url + match_link.replace('info', 'live')
        match_link_scorecard = base_url + match_link.replace('info', 'scorecard')

        live_scraper = Scraper(match_link=match_link_live, isMonitoring=True)
        scorecard_scraper = Scraper(match_link=match_link_scorecard, isMonitoring=True)

        start_time = time.time()
        max_duration = 60 * 60 * 3  # 3 hours

        while True:
            live_data = live_scraper.scrape_match_live_feed(match_link_live)
            scorecard_data = scorecard_scraper.scrape_match_scorecard(match_link_scorecard)

            live_data["match_id"] = str(match_id)
            scorecard_data["match_id"] = str(match_id)

            save_to_db(live_page_collection, live_data, unique_field=match_id)
            save_to_db(scorecard_collection, scorecard_data, unique_field=match_id)

            if "player_of_the_match" in live_data.keys():
                logger.info(f"Match ID {match_id} finished. Player of the match: {live_data.get('player_of_the_match')}")
                break

            if time.time() - start_time > max_duration:
                logger.warning(f"Match ID {match_id} scraping timed out after 3 hours.")
                break

            logger.debug(f"Updated data for match ID {match_id}")
            time.sleep(2)

    except Exception as e:
        logger.error(f"Error occurred during live scraping for match ID {match_id}: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    schedule_jobs()