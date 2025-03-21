#!/bin/python3

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import threading
import time
from plyer import notification
import platform
import logging

# Configure logging
def setup_logging():
    home_dir = os.path.expanduser('~')
    if platform.system() == "Windows":
        local_dir = os.path.join(home_dir, 'AppData', 'Local', 'NotifyDude')
    elif platform.system() == "Darwin":  # macOS
        local_dir = os.path.join(home_dir, 'Library', 'Application Support', 'NotifyDude')
    else:
        local_dir = os.path.join(home_dir, '.local', 'NotifyDude')

    os.makedirs(local_dir, exist_ok=True)
    log_path = os.path.join(local_dir, 'error_log.txt')

    logging.basicConfig(
        filename=log_path,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def check_internet_connection():
    try:
        requests.get('https://8.8.8.8', timeout=5)
        return True
    except requests.ConnectionError:
        return False


def fetch_notices(url, site_name):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Define cross-platform path for seen notices
        home_dir = os.path.expanduser('~')
        if platform.system() == "Windows":
            local_dir = os.path.join(home_dir, 'AppData', 'Local', 'NotifyDude')
        elif platform.system() == "Darwin":  # macOS
            local_dir = os.path.join(home_dir, 'Library', 'Application Support', 'NotifyDude')
        else:
            local_dir = os.path.join(home_dir, '.local', 'NotifyDude')

        os.makedirs(local_dir, exist_ok=True)
        seen_notices_path = os.path.join(local_dir, 'seen_notices.txt')
        log_path = os.path.join(local_dir, 'log.txt')
        logo_path = os.path.join(local_dir, 'logo_gray.png')  # Ensure this exists or skip `app_icon`

        # Load previously seen notices from seen_notices.txt
        try:
            with open(seen_notices_path, 'r') as f:
                seen_notices = set(line.strip() for line in f)
        except FileNotFoundError:
            open(seen_notices_path, 'w').close()  # Create the file if not found
            seen_notices = set()

        # Get today's date for filtering notices
        today = datetime.today().strftime('%B %d, %Y')
        today_dt = datetime.strptime(today, '%B %d, %Y')

        ten_days_ago_dt = today_dt - timedelta(days=30)
        
        data = soup.find_all('div', class_='notice')
        new_notices = []
        for d in data:
            title = d.find('div', class_='title').text.strip()
            date = d.find('span', class_='date').text.strip()

            # Find the <a> tag within the <div> with class 'title'
            a_tag = d.find('div', class_='title').find('a')
            # Extract the href attribute
            link = a_tag['href']

            notice = f"{date}: {title} Link: {link}".strip()

            # Check if notice is new
            date = str(date).strip()
            notice_date = datetime.strptime(date, '%B %d, %Y')

            if notice not in seen_notices and ten_days_ago_dt <= notice_date <= today_dt:
                new_notices.append(notice)
                seen_notices.add(notice)  # Mark as seen

        # Send notifications for new notices
        for notice in new_notices:
            notification.notify(
                title=site_name,
                message=notice,
                app_name='NotifyDude',
                app_icon=logo_path,
                timeout=10
            )

        # Save updated seen notices
        with open(seen_notices_path, 'w') as f:
            for notice in seen_notices:
                f.write(notice + '\n')

        with open(log_path, 'a') as f:
            f.write(f'Checked {site_name} on {datetime.now()}\n')
        
        print(f'{datetime.now()} - fetching {site_name} done')

    except requests.RequestException as e:
        logging.error(f"Request failed for {site_name}: {e}")
    except Exception as e:
        logging.error(f"An error occurred while fetching notices from {site_name}: {e}")
        

def __main__():
    setup_logging()
    uiu_url = 'https://uiu.ac.bd/notice'
    cse_url = 'https://cse.uiu.ac.bd/notice'

    # Run the fetch loop periodically
    while True:

        while not check_internet_connection():
            print("No internet connection. Retrying ...")
            time.sleep(1)

        try:
            if check_internet_connection():
                thread_uiu = threading.Thread(target=fetch_notices, args=(uiu_url, 'UIU'))
                thread_cse = threading.Thread(target=fetch_notices, args=(cse_url, 'CSE'))

                # Start threads
                thread_uiu.start()
                thread_cse.start()

                # Wait for threads to finish
                thread_uiu.join()
                thread_cse.join()
            else:
                print(f"{datetime.now()} - No internet connection. Retrying in 10 minutes...")
                logging.warning("No internet connection. Retrying in 10 minutes...")

            time.sleep(600)  # Wait 10 minutes before checking again

        except Exception as e:
            logging.error(f"An error occurred in the main loop: {e}")
            time.sleep(600)  # Wait 10 minutes before retrying

# Start the program
__main__()