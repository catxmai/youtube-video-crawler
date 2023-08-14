from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *

import time
import re
import csv
import traceback
import random

def create_driver(headless, user_data_dir=""):

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1540,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    if headless:
        options.add_argument("--headless=new")

    if user_data_dir:
        options.add_argument("user-data-dir=" + user_data_dir)

    driver = webdriver.Chrome(options = options)

    return driver

def click_video_tab(driver, tab):
    # tab names: Latest, Popular, Oldest

    video_tab_selector = driver.find_element(By.CSS_SELECTOR, "iron-selector#chips")
    video_tab = video_tab_selector.find_element(By.CSS_SELECTOR, f"yt-formatted-string[title='{tab}']")
    driver.execute_script("arguments[0].click();", video_tab)

def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

def get_scroll_height(driver):
    return driver.execute_script("return document.documentElement.scrollHeight") 

def get_video_elements(driver):

    videos = driver.find_elements(By.CSS_SELECTOR, "#contents > ytd-rich-grid-row")
    return videos

def parse_video_from_element(video_element):

    video_title_link = video_element.find_element(By.CSS_SELECTOR, "a#video-title-link")
    video_title = video_title_link.get_attribute("title")
    video_href = video_title_link.get_attribute("href")

    pattern = r"(?<=watch\?v=)\S*" 
    video_id = re.search(pattern, video_href)[0]

    return video_id, video_title
    

def get_video_list(driver, run_id, channel_name, count_goal):

    video_id_list, video_title_list = [], []
    current_count_on_page = len(get_video_elements(driver))

    with open(f"output_{channel_name}_{run_id}.csv", 'w', encoding="utf-8") as f:
        writer = csv.writer(f, delimiter = ",", lineterminator = "\n")
        writer.writerow(["video_id", "channel_name", "video_title"])

    while (current_count_on_page < count_goal):
    
        current_height = get_scroll_height(driver)

        scroll_pause_time = random.uniform(5.0, 20.0)
        save_freq = random.randint(1, 5)
        for _ in range(save_freq):
            scroll_to_bottom(driver)
            time.sleep(scroll_pause_time)

        # check scroll difference. try again once, if not then break
        height_diff = current_height - get_scroll_height(driver)
        if height_diff == 0:
            time.sleep(5)
            scroll_to_bottom(driver)
            time.sleep(5)
            scroll_to_bottom(driver)
            time.sleep(5)
            
        video_elements = get_video_elements(driver)[len(video_id_list):]
        for elem in video_elements:
            video_id, video_title = parse_video_from_element(elem)
            video_id_list.append(video_id)
            video_title_list.append(video_title)

            with open(f"output_{channel_name}_{run_id}.csv", 'a', encoding="utf-8") as f:
                writer = csv.writer(f, delimiter = ",", lineterminator = "\n")
                writer.writerow([video_id, channel_name, video_title])

        current_count_on_page = len(get_video_elements(driver))

        height_diff = current_height - get_scroll_height(driver)
        if height_diff == 0:
            # replace with some end of list check before raising error
            print("can't scroll more to bottom")
            raise AssertionError("can't scroll more to bottom")

    return video_id_list, video_title_list
    


if __name__ == "__main__":

    repeat_count = 2
    channel_list = [
        ("Numberphile", "https://www.youtube.com/@numberphile/videos"),
        ("CGP Grey", "https://www.youtube.com/@CGPGrey/videos"),
        ("Computerphile", "https://www.youtube.com/@Computerphile/videos"),
        ("MindYourDecisions", "https://www.youtube.com/@MindYourDecisions/videos"),
        ("3Blue1Brown", "https://www.youtube.com/@3blue1brown/videos"),
        ("Standup Maths", "https://www.youtube.com/@standupmaths/videos"),
        ("Steve Mould", "https://www.youtube.com/@SteveMould/videos"),
        ("Veritasium", "https://www.youtube.com/@veritasium/videos"),
        ("LockPickingLawyer", "https://www.youtube.com/@lockpickinglawyer/videos"),
        ("TheBackyardScientist", "https://www.youtube.com/@TheBackyardScientist/videos"),
        ("Code Bullet", "https://www.youtube.com/@CodeBullet/videos"),
        ("The Action Lab ", "https://www.youtube.com/@TheActionLab/videos"),
        ("TKOR", "https://www.youtube.com/@TheKingofRandom/videos"),
        ("Boston Dynamics", "https://www.youtube.com/@BostonDynamics/videos"),
    ]

    for run_id in range(repeat_count):
        for channel_name, channel_url in channel_list:
            driver = create_driver(headless=False, user_data_dir="C:\\Users\\cmai\\Documents\\UserData_happysquare88")
            driver.get(channel_url)
            channel_name = channel_name.replace(" ", "")

            WebDriverWait(driver, 2).until(EC.presence_of_element_located(('id', 'contents')))
            click_video_tab(driver, "Popular")

            try:
                video_id_list, video_title_list = get_video_list(driver,
                                                                 run_id,
                                                                 channel_name,
                                                                 count_goal=1000)
            except Exception as e:
                print(traceback.format_exc())
                driver.quit()
                continue
            
            driver.quit()
            
