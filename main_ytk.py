from utils import *

import time
import pandas as pd
import os


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


def parse_playlist_link(playlist_element) -> str:

    playlist_link = playlist_element.find_element(By.CSS_SELECTOR, "#playlist-link").get_attribute("href")
    return playlist_link

def get_videos_from_playlist(playlist_link) -> tuple:

    titles, ids = [], []

    time.sleep(2)
    driver.get(playlist_link)
    time.sleep(2)

    playlist_videos = driver.find_elements(By.CSS_SELECTOR, "#related.style-scope.ytk-two-column-watch-next-results-renderer > ytk-compact-video-renderer")
    for vid in playlist_videos:
        title, vid_id = parse_video_element(vid)
        titles.append(title)
        ids.append(vid_id)

    return titles, ids


def crawl_ytk(driver) -> pd.DataFrame:

    titles, ids, cates = [], [], []
    found_playlists = []

    tabs = get_tabs(driver)
    for tab in tabs:

        click(driver, tab)
        time.sleep(2)
        # tab_name = tab.get_attribute("title")
        videos, playlists = get_video_parent_lists(driver)
        found_playlists.extend(playlists)

        for video in videos:
            title, id = parse_video_element(video)
            titles.append(title)
            ids.append(id)
            # cates.append(tab_name)

    playlist_links = [parse_playlist_link(pl_elem) for pl_elem in found_playlists]
    playlist_links = list(set(playlist_links))
    for link in playlist_links:
        ptitles, pids = get_videos_from_playlist(link)
        titles.extend(ptitles)
        ids.extend(pids)

    df = pd.DataFrame(
        {
            'video_id': ids,
            'video_title': titles,
            # 'category': cates
        }
    )
    return df

if __name__ == "__main__":

    dirs = ['output', 'output_ytk']
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)

    driver = create_driver(headless=False, user_data_dir="C:\\Users\\cmai\\Documents\\UserData_happysquare88")
    driver.get("https://www.youtubekids.com/")
    driver_wait(driver, 45, By.CSS_SELECTOR, "#page-root > ytk-kids-home-screen-renderer > #content")

    timestamp = get_timestamp()
    df = crawl_ytk(driver)

    df.drop_duplicates(subset=['video_id'], inplace=True)
    df.reset_index(inplace=True, drop=True)
    df.to_csv(f"output_ytk/{timestamp}.csv", index=False)