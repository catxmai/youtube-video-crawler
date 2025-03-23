from utils import *

import time
import pandas as pd
import os
import csv
import sys

from collections import deque

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
    vid_id = parse_video_id(vid_elem.get_attribute("href"))

    return vid_id, title


def parse_playlist_link(playlist_element) -> str:

    playlist_link = playlist_element.find_element(By.CSS_SELECTOR, "#playlist-link").get_attribute("href")
    return playlist_link


def crawl_recommendations(driver, url) -> tuple:

    # return watch next videos on a particular video/playlist page

    time.sleep(1)
    driver.get(url)
    ids, titles = [], []

    try:
        driver_wait(driver, 15, (By.CSS_SELECTOR, "#related.style-scope"))
    except TimeoutException:
        return ids, titles


    time.sleep(1)
    scroll_to_bottom(driver)
    time.sleep(2)

    playlist_videos = driver.find_elements(
        By.CSS_SELECTOR,
        "#related.style-scope.ytk-two-column-watch-next-results-renderer > ytk-compact-video-renderer"
    )
    # print(len(playlist_videos)) # 20 recommendations per video
    for vid in playlist_videos:
        vid_id, title = parse_video_element(vid)
        ids.append(vid_id)
        titles.append(title)

    return ids, titles



def _crawl_ytk_homepage(driver) -> pd.DataFrame:

    ids, titles = [], []
    cates =  []
    found_playlists = []

    tabs = get_tabs(driver)
    for tab in tabs:

        jsclick(driver, tab)
        time.sleep(2)
        tab_name = tab.get_attribute("title")
        videos, playlists = get_video_parent_lists(driver)
        found_playlists.extend(playlists)

        for video in videos:
            id, title = parse_video_element(video)
            ids.append(id)
            titles.append(title)
            cates.append(tab_name)

    # playlist_links = [parse_playlist_link(pl_elem) for pl_elem in found_playlists]
    # playlist_links = dedupe(playlist_links)
    # for link in playlist_links:
    #     pids, ptitles = crawl_recommendations(driver, link)
    #     ids.extend(pids)
    #     titles.extend(ptitles)

    df = pd.DataFrame(
        {
            'video_id': ids,
            'video_title': titles,
            'category': cates
        }
    )
    return df


def crawl_from_homepage(driver) -> pd.DataFrame:

    driver.get("https://www.youtubekids.com/")
    driver_wait(driver, 50, (By.CSS_SELECTOR, "#page-root > ytk-kids-home-screen-renderer > #content"))

    df = _crawl_ytk_homepage(driver)

    df.drop_duplicates(subset=['video_id'], inplace=True)
    df.reset_index(inplace=True, drop=True)

    return df


def crawl_from_videos(driver, video_id_list, branching=False, max_result_count=100) -> list:

    # BFS from video_list. Search more from results with branching=True

    timestamp = get_timestamp()
    output_file = open(f"output_ytk/ytk_recs_{timestamp}.csv", "w", encoding="utf-8")
    output_writer = csv.writer(output_file,
								delimiter = ",",
								quotechar = '"',
								quoting = csv.QUOTE_MINIMAL,
								lineterminator = "\n")
    
    unique_id_list = dedupe(video_id_list)
    already_seen = set()
    to_crawl = deque()
    all_result_ids = set()
    current_result_count = 0

    # initialize to_crawl
    for video_id in unique_id_list:
        to_crawl.append(video_id)

    # already_seen = set(pd.read_csv("output_ytk/ytk_recs_03202025_2110.csv")["video_id"])

    output_writer.writerow(['video_id', 'video_url', 'ytk_url', 'video_title'])

    while to_crawl and current_result_count < max_result_count:
        video_id = to_crawl.popleft()

        if video_id not in already_seen:
            already_seen.add(video_id)

            result_ids, result_titles = crawl_recommendations(driver, urlk(video_id))

            for result_id, result_title in zip(result_ids, result_titles):
    
                if result_id not in all_result_ids:
                    output_writer.writerow([result_id,
                                            url(result_id),
                                            urlk(result_id),
                                            result_title])
                    all_result_ids.add(result_id)
                    current_result_count += 1

                    # force write to disk. relatively expensive but data/logs is more important
                    output_file.flush()
                    os.fsync(output_file)

            if branching and current_result_count < max_result_count:
                for video_id in result_ids:
                    if video_id not in already_seen:
                        to_crawl.append(video_id)

    output_file.close()
    return list(all_result_ids)


if __name__ == "__main__":

    dirs = ['output', 'output_ytk']
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)

    mode = "branch"
    headless = False
    input_file = "output_ytk/ytk_home_03202025_1915.csv"

    args = sys.argv[1:]
    if args:
        mode = args[0] # mode is "home" or "branch"
        headless = boolify(args[1])
        if mode == "branch":
            try:
                input_file = args[2]
            except:
                raise InvalidArgumentException()
    

    driver = create_driver(headless=headless, user_data_dir="C:\\Users\\cmai\\Documents\\UserData_hapysquare88")
    driver.get("https://www.youtubekids.com/")
    time.sleep(60)

    start_time = time.time()

    if mode == "branch":

        id_list = pd.read_csv(input_file)["video_id"]
        result = crawl_from_videos(driver,
                                id_list,
                                branching=True,
                                max_result_count=50000)
    
    if mode == "home":
        result = crawl_from_homepage(driver)
        timestamp = get_timestamp()
        result.to_csv(f"output_ytk/ytk_home_{timestamp}.csv", index=False)

    duration = time.time() - start_time
    print(f"Finished in {duration}s")


    