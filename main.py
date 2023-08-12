from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *

import time
import re
import csv

def create_driver(headless):

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1540,1080")
    options.add_argument("--disable-extensions")
    if headless:
        options.add_argument("--headless=new")

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

    video_parent = driver.find_element(By.CSS_SELECTOR, "#contents")
    videos = video_parent.find_elements(By.CSS_SELECTOR, "ytd-rich-grid-row")
    return videos

def parse_video_from_element(video_element):

    video_title_link = video_element.find_element(By.CSS_SELECTOR, "a#video-title-link")
    video_title = video_title_link.get_attribute("title")
    video_href = video_title_link.get_attribute("href")

    pattern = r"(?<=watch\?v=)\S*" 
    video_id = re.search(pattern, video_href)[0]

    return video_id, video_title
    

def get_video_list(driver, count_goal, save_freq, scroll_pause_time):

    video_id_list, video_title_list = [], []
    current_count_on_page = len(get_video_elements(driver))

    with open("output.csv", 'w') as f:
        writer = csv.writer(f, delimiter = ",", lineterminator = "\n")
        writer.writerow(["video_id", "video_title"])

    while (current_count_on_page < count_goal):
    
        current_height = get_scroll_height(driver)

        for _ in range(save_freq):
            scroll_to_bottom(driver)
            time.sleep(scroll_pause_time)

        # check scroll difference. try again once, if not then break
        height_diff = current_height - get_scroll_height(driver)
        if height_diff == 0:
            time.sleep(15)
            scroll_to_bottom(driver)
            time.sleep(scroll_pause_time)

            height_diff = current_height - get_scroll_height(driver)
            if height_diff == 0:
                # replace with some end of list check before raising error
                raise RuntimeError("can't scroll more to bottom")
            
        video_elements = get_video_elements(driver)[len(video_id_list):]
        for elem in video_elements:
            video_id, video_title = parse_video_from_element(elem)
            video_id_list.append(video_id)
            video_title_list.append(video_title)

            with open("output.csv", 'a') as f:
                writer = csv.writer(f, delimiter = ",", lineterminator = "\n")
                writer.writerow([video_id, video_title])

        current_count_on_page = len(get_video_elements(driver))

    return video_id_list, video_title_list
    


if __name__ == "__main__":

    driver = create_driver(headless=False)

    channel_url = "https://www.youtube.com/@ABCNews/videos"
    driver.get(channel_url)

    WebDriverWait(driver, 2).until(EC.presence_of_element_located(('id', 'contents')))
    click_video_tab(driver, "Popular")
    video_id_list, video_title_list = get_video_list(driver, count_goal=10000, save_freq=5, scroll_pause_time=2)
    print(video_id_list)
    print(len(video_id_list))
