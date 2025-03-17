from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *

import re
import datetime
import urllib.request
import json
import os
import time
import pandas as pd

from collections import deque


from io import BytesIO
import zipfile


def dedupe(arr) -> list:

    # better way to remove duplicates? since this way order is lost
    return list(set(arr))

def urlk(youtube_video_id:str) -> str:

    youtube_video_id = youtube_video_id.strip()
    assert(len(youtube_video_id) == 11)

    return "https://www.youtubekids.com/watch?v=" + youtube_video_id


def url(youtube_video_id:str) -> str:

    youtube_video_id = youtube_video_id.strip()
    assert(len(youtube_video_id) == 11)

    return "https://www.youtube.com/watch?v=" + youtube_video_id

# thousand, million, billion mapping
digits = {
    'k': 3,
    'm': 6,
    'b': 9
}
def str_to_num(num_str:str) -> int:
    if num_str[-1].lower() in digits:
        num, magnitude = num_str[:-1], num_str[-1]
        ret_val = float(num) * 10 ** (digits[magnitude])
        return int(ret_val)
    else:
        try:
            ret_val = int(num_str)
            return ret_val
        except:
            raise TypeError('bad arg')


def create_driver(headless:bool, user_data_dir="") -> webdriver.Chrome:

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1540,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")


    if headless:
        options.add_argument("--headless=new")

    if len(user_data_dir) > 0:
        options.add_argument("user-data-dir=" + user_data_dir)

    try:
        driver = webdriver.Chrome(options=options)
    except SessionNotCreatedException as e:
        major_version = parse_driver_version_from_error(e.msg)

        if major_version == 0:
            raise Exception('cannot find major version from error msg')
        
        install_chromedriver(major_version=major_version)
        driver = webdriver.Chrome(options=options)

    return driver


def parse_driver_version_from_error(msg:str) -> str:
    # parsing driver version from SessionNotCreated error
    msg = msg.lower()

    if "this version of chromedriver only supports" not in msg:
        return 0
    
    pattern = r"(?<=current browser version is ).+(?= with binary path)"
    match = re.search(pattern, msg)
    if not match:
        return 0
    major_version = match[0].split(".")[0] # version: 130.0.6723.69, major version: 130

    return major_version

def install_chromedriver(major_version:str):
    
    milestone_url = "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json"
    # get matched download url
    with urllib.request.urlopen(milestone_url) as url:
        data = json.load(url)
        milestone = data['milestones'].get(major_version)
        dl_url = milestone['downloads']['chromedriver'][3]['url'] # download link for win32

    # download the binary
    response = urllib.request.urlopen(dl_url)
    zip = BytesIO(response.read())

    with zipfile.ZipFile(zip) as zip_file:
        for zip_info in zip_file.infolist():
            if zip_info.filename.endswith("chromedriver.exe"):
                zip_info.filename = os.path.basename(zip_info.filename)
                zip_file.extract(zip_info)
                break

def parse_video_id(href) -> str:

    pattern = r"(?<=watch\?v=).{11}" # capture anything 11-char after v=
    video_id = re.search(pattern, href)

    if video_id:
        return video_id[0]

    return None

def parse_reel_id(href) -> str:

    pattern = r"(?<=shorts\/).{11}" # capture anything 11-char after v=
    reel_id = re.search(pattern, href)

    if reel_id:
        return reel_id[0]

    return None

def get_video_title(driver):
    try:
        title = driver.find_element(By.CSS_SELECTOR, "div#above-the-fold h1 yt-formatted-string").get_attribute("title")
        return title
    except (TypeError, KeyError) as e:
        return None


def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

def scroll_to_top(driver):
    driver.execute_script("window.scrollTo(0, 0);")


def get_scroll_height(driver) -> int:
    return driver.execute_script("return document.documentElement.scrollHeight") 

def jsclick(driver, elem):
    driver.execute_script("arguments[0].click();", elem)


def get_timestamp() -> str:

    # Generates an id for scraping run based on system time
    d = datetime.datetime.now()
    test_str = '{date:%m%d%Y_%H%M}'.format(date = d)

    return test_str

def driver_wait(driver, wait_time, element_tuple):

    # throws selenium.common.exceptions.TimeoutException

    WebDriverWait(driver, wait_time).until(
        EC.presence_of_element_located(element_tuple)
    )


def is_for_kids(driver):

    try:
        script_elem = driver.find_element(By.CSS_SELECTOR, "div#watch7-content + script")
        script_text = script_elem.get_attribute("innerHTML")
        if 'for kid' in script_text:
            return True
        
        ytk_ad = driver.find_element(By.CSS_SELECTOR, "#teaser-carousel")
        ad_link = ytk_ad.find_element(By.CSS_SELECTOR, "a").get_attribute("href").strip()
        if "ytkids" in ad_link:
            return True
        
        ad_text = ytk_ad.find_element(By.CSS_SELECTOR, ".YtCarouselTitleViewModelTitle").get_attribute("innerHTML").lower()
        if "youtube kids" in ad_text:
            return True
        
    except NoSuchElementException:
        pass

    return False


def get_side_ad_site(driver):

    # site is usually the link to advertiser's site, but sometimes it's just the site name

    try:
        side_ad_container = driver.find_element(By.CSS_SELECTOR, ".ytwAdDetailsLineViewModelHostIsClickableAdComponent span")
        site = side_ad_container.get_attribute("innerHTML").strip()
        return site

    except NoSuchElementException:
        return None

def get_side_ad_text_and_link(driver):
    title, body = "", ""
    href = None

    try:
        title_box = driver.find_elements(By.CSS_SELECTOR, ".ytwFeedAdMetadataViewModelHostMetadata span a a")
        title = title_box[0].get_attribute("innerHTML").strip()
        href = title_box[0].get_attribute('href')
    except IndexError:
        pass

    try:
        body_container = driver.find_elements(By.CSS_SELECTOR, ".ytwFeedAdMetadataViewModelHostMetadata span a a")
        body = body_container[1].get_attribute("innerHTML").strip()
    except IndexError:
        pass

    text = title + body
    text = text if len(text) > 0 else None
    return text, href

def get_side_ad_text(driver):
    return get_side_ad_text_and_link(driver)[0]

def get_side_ad_link(driver):
    return get_side_ad_text_and_link(driver)[1]

def get_side_ad_img(driver):

    img_src = None

    try:
        img_src = driver.find_element(
            By.CSS_SELECTOR,
            ".ytwSquareImageLayoutViewModelHostImage .ytwAdImageViewModelHostImageContainer img"
        ).get_attribute("src")
    except NoSuchElementException:
        pass

    return img_src


def pause_video(driver: webdriver.Chrome):

    play_button = driver.find_element(
        By.CSS_SELECTOR, "button.ytp-play-button.ytp-button"
    )
    if play_button:
        status = play_button.get_attribute("data-title-no-tooltip")

        if status == "Pause":
            try:
                play_button.send_keys("k")
            except ElementNotInteractableException:
                pass



def play_video(driver: webdriver.Chrome):

    try:
        driver_wait(driver, 5, (By.CSS_SELECTOR, "button.ytp-play-button.ytp-button"))
    except:
        raise NoSuchElementException("no play button")

    play_button = driver.find_element(
        By.CSS_SELECTOR, "button.ytp-play-button.ytp-button"
    )
    status = play_button.get_attribute("data-title-no-tooltip")

    if status == "Play":
        play_button.send_keys("k")



def skip_ad(driver: webdriver.Chrome):
    # assuming driver has ad
    skip_ad_button = (By.CSS_SELECTOR, 'button.ytp-skip-ad-button')

    def click_skip_button(driver):
        skip_button = driver.find_element(skip_ad_button[0], skip_ad_button[1])
        # jsclick(driver, skip_button)
        skip_button.click()

    try:
        play_video(driver)
        time.sleep(5)
        pause_video(driver)

        time.sleep(1)
        click_skip_button(driver)

    except (NoSuchElementException, ElementNotInteractableException, TimeoutException) as e:
        try:
            play_video(driver)
            driver_wait(driver, 6, skip_ad_button)
            click_skip_button(driver)
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as e:
            pass

            




