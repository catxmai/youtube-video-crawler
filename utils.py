from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *

import re
import datetime

def create_driver(headless, user_data_dir="") -> webdriver.Chrome:

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

def parse_vid_id(href) -> str:

    pattern = r"(?<=watch\?v=).{11}" # capture anything 11-char after v=
    video_id = re.search(pattern, href)

    if video_id:
        return video_id[0]

    return None


def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

def get_scroll_height(driver):
    return driver.execute_script("return document.documentElement.scrollHeight") 

def click(driver, elem):
    driver.execute_script("arguments[0].click();", elem)


def get_timestamp() -> str:

    # Generates an id for scraping run based on system time
    d = datetime.datetime.now()
    test_str = '{date:%m%d_%H%M}'.format(date = d)

    return test_str

def driver_wait(driver, wait_time, by_attr, element_string):

    WebDriverWait(driver, wait_time).until(EC.presence_of_element_located(
            (by_attr, element_string)
    ))