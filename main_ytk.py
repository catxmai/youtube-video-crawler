from utils import *

import time
import pandas as pd


def get_tabs(driver) -> list:

    tab_elems = driver.find_elements(By.CSS_SELECTOR, "#anchors-row-content.style-scope.ytk-masthead > ytk-kids-category-tab-renderer")
    return tab_elems

def get_video_parent_lists(driver) -> tuple:

    parent_css = "#contents.style-scope.ytk-item-section-renderer"
    playlists = driver.find_elements(By.CSS_SELECTOR, f"{parent_css} > ytk-compact-playlist-renderer")
    videos = driver.find_elements(By.CSS_SELECTOR, f"{parent_css} > ytk-compact-video-renderer")
    
    return videos, playlists


def parse_video_element(video_element) -> tuple:

    vid_elem = video_element.find_element(By.CSS_SELECTOR, "a.ytk-compact-video-renderer")
    title = vid_elem.get_attribute("title")
    vid_id = parse_vid_id(vid_elem.get_attribute("href"))

    return title, vid_id

if __name__ == "__main__":

    driver = create_driver(headless=False, user_data_dir="C:\\Users\\cmai\\Documents\\UserData_happysquare88")
    driver.get("https://www.youtubekids.com/")
    time.sleep(15)

    titles, ids, cates = [], [], []

    tabs = get_tabs(driver)
    for tab in tabs:

        click(driver, tab)
        time.sleep(5)
        tab_name = tab.get_attribute("title")
        videos, playlists = get_video_parent_lists(driver)
        for v in videos:
            title, id = parse_video_element(v)
            titles.append(title)
            ids.append(id)
            cates.append(tab_name)

    df = pd.DataFrame(
        {
            'video_id': ids,
            'video_title': titles,
            'category': cates
        }
    )
    df.to_csv("output_ytk.csv", index=False)