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

    if headless:
        options.add_argument("--headless=new")

    if user_data_dir:
        options.add_argument("user-data-dir=" + user_data_dir)

    try:
        driver = webdriver.Chrome(options=options)
    except SessionNotCreatedException as e:
        major_version = parse_driver_version_from_error(e.msg)

        if major_version == 0:
            raise Exception('cannot find major version')
        
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

def parse_vid_id(href) -> str:

    pattern = r"(?<=watch\?v=).{11}" # capture anything 11-char after v=
    video_id = re.search(pattern, href)

    if video_id:
        return video_id[0]

    return None


def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")

def get_scroll_height(driver) -> int:
    return driver.execute_script("return document.documentElement.scrollHeight") 

def click(driver, elem):
    driver.execute_script("arguments[0].click();", elem)


def get_timestamp() -> str:

    # Generates an id for scraping run based on system time
    d = datetime.datetime.now()
    test_str = '{date:%m%d_%H%M}'.format(date = d)

    return test_str

def driver_wait(driver, wait_time, element_tuple):

    # throws selenium.common.exceptions.TimeoutException

    WebDriverWait(driver, wait_time).until(
        EC.presence_of_element_located(element_tuple)
    )