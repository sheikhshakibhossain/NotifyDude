#!/bin/python3

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import threading
import time
from plyer import notification
import platform


def fetch_notices(url, site_name):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Define cross-platform path for seen notices
    home_dir = os.path.expanduser('~')
    if platform.system() == "Windows":
        local_dir = os.path.join(home_dir, 'AppData', 'Local', 'uiu_notification')
    elif platform.system() == "Darwin":  # macOS
        local_dir = os.path.join(home_dir, 'Library', 'Application Support', 'uiu_notification')
    else:
        local_dir = os.path.join(home_dir, '.local', 'uiu_notification')

    os.makedirs(local_dir, exist_ok=True)
    seen_notices_path = os.path.join(local_dir, 'seen_notices.txt')
    logo_path = os.path.join(local_dir, 'logo.png')  # Ensure this exists or skip `app_icon`

    # Load previously seen notices from seen_notices.txt
    try:
        with open(seen_notices_path, 'r') as f:
            seen_notices = set(line.strip() for line in f)
    except FileNotFoundError:
        open(seen_notices_path, 'w').close()  # Create the file if not found
        seen_notices = set()

    # Get today's date for filtering notices
    today = datetime.today().strftime('%B %d, %Y')
    data = soup.find_all('div', class_='notice')
    new_notices = []
    for d in data:
        title = d.find('div', class_='title').text.strip()
        date = d.find('span', class_='date').text.strip()
        notice = f'{date}: {title}'

        # Check if notice is new
        if date == today or notice not in seen_notices:
            new_notices.append(notice)
            seen_notices.add(notice)  # Mark as seen

    # Send notifications for new notices
    for notice in new_notices:
        notification.notify(
            title=site_name,
            message=notice,
            app_name=f'{site_name} Notification',
            app_icon=logo_path if os.path.exists(logo_path) else None,
            timeout=10
        )

    # Save updated seen notices
    with open(seen_notices_path, 'w') as f:
        for notice in seen_notices:
            f.write(notice + '\n')


def __main__():
    uiu_url = 'https://uiu.ac.bd/notice'
    cse_url = 'https://cse.uiu.ac.bd/notice'

    # Run the fetch loop periodically
    while True:
        thread_uiu = threading.Thread(target=fetch_notices, args=(uiu_url, 'UIU'))
        thread_cse = threading.Thread(target=fetch_notices, args=(cse_url, 'CSE'))

        # Start threads
        thread_uiu.start()
        thread_cse.start()

        # Wait for threads to finish
        thread_uiu.join()
        thread_cse.join()

        time.sleep(600)  # Wait 10 minutes before checking again


# Start the program
__main__()
