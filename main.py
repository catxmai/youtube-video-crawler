from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *

import time
import csv
import traceback
import random
import json

from utils import *

def click_video_tab(driver, tab):
    # tab names: Latest, Popular, Oldest

    video_tab_selector = driver.find_element(By.CSS_SELECTOR, "iron-selector#chips")
    video_tab = video_tab_selector.find_element(By.CSS_SELECTOR, f"yt-formatted-string[title='{tab}']")
    click(driver, video_tab)

def get_video_elements(driver):

    videos = driver.find_elements(By.CSS_SELECTOR, "#contents > ytd-rich-grid-row")
    return videos

def parse_video_from_element(video_element):

    video_title_link = video_element.find_element(By.CSS_SELECTOR, "a#video-title-link")
    video_title = video_title_link.get_attribute("title")
    video_href = video_title_link.get_attribute("href")
    video_id = parse_vid_id(video_href)

    return video_id, video_title
    

def get_video_list(driver, run_id, channel_name, count_goal, output_dir):

    video_id_list, video_title_list = [], []
    current_count_on_page = len(get_video_elements(driver))

    f = open(f"{output_dir}/output_{channel_name}_{run_id}.csv", 'w', encoding="utf-8")

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

            writer = csv.writer(f, delimiter = ",", lineterminator = "\n")
            writer.writerow([video_id, channel_name, video_title])

        current_count_on_page = len(get_video_elements(driver))

        height_diff = current_height - get_scroll_height(driver)
        if height_diff == 0:
            # replace with some end of list check before raising error
            print("can't scroll more to bottom")
            raise AssertionError("can't scroll more to bottom")

    return video_id_list, video_title_list


def handle_strange_redirect(driver, channel_name):

    driver.get(f"https://www.youtube.com/results?search_query={channel_name}")
    avatar = driver.find_element(By.CSS_SELECTOR, "#avatar-section > a")
    click(driver, avatar)

    time.sleep(2)
    tab_bar = driver.find_element(By.CSS_SELECTOR, "#tabsContent")
    tabs = tab_bar.find_elements(By.CSS_SELECTOR, "div.tab-title.style-scope.ytd-c4-tabbed-header-renderer")
    for tab in tabs:
        if tab.get_attribute("innerHTML").lower() == "videos":
            click(driver, tab)
            break

    time.sleep(3)


if __name__ == "__main__":

    repeat_count = 10
    f = open("news_channel_list.json", "r")
    channel_list = json.load(f)["channels"]
    channels_to_run = ['MarketBeat','HarvardBusinessReview','Gallup','Militarycom',"Ballotpedia",'Justia','Pew','PRNewswire','TechSpot']

    for rid in range(repeat_count):
        run_id = rid+3
        for channel_name, channel_url in channel_list:
            channel_name = channel_name.replace(" ", "")

            if channel_name in channels_to_run:
                driver = create_driver(headless=False, user_data_dir="C:\\Users\\cmai\\Documents\\UserData_happysquare88")
                driver.get(channel_url)
                try:
                    WebDriverWait(driver, 2).until(EC.presence_of_element_located(('id', 'contents')))
                    click_video_tab(driver, "Popular")
                    
                except:
                    handle_strange_redirect(driver, channel_name)
                    
                try:
                    click_video_tab(driver, "Popular")
                    video_id_list, video_title_list = get_video_list(driver,
                                                                    run_id,
                                                                    channel_name,
                                                                    count_goal=100,
                                                                    output_dir="outputs_news")
                except Exception as e:
                    print(traceback.format_exc())
                    print(channel_name)
                    print(channel_url)
                    driver.quit()
                    continue
                
                driver.quit()
            
