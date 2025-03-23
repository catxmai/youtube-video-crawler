from utils import *

import random

def watch_video(driver, duration=30):

    play_video(driver)
    time.sleep(6)
    skip_ad(driver)

    # can watch a bit more than the actual requested duration
    play_video(driver)
    time.sleep(duration)

def crawl_recommendations(driver, url, target_count=50) -> dict:

    # chips/tabs above content recs
    # 3 content components: ad, reels, and recs

    def get_tabs(driver) -> list:
        tabs = driver.find_elements(By.CSS_SELECTOR, "div.style-scope.yt-chip-cloud-renderer yt-chip-cloud-chip-renderer yt-formatted-string")
        tab_texts = [elem.get_attribute('title') for elem in tabs]
        return tab_texts


    def get_upnext_lists(driver, target_count) -> tuple:

        parent_css = "#items.style-scope.ytd-watch-next-secondary-results-renderer"
        playlists = driver.find_elements(By.CSS_SELECTOR, f"{parent_css} yt-lockup-view-model")

        videos = []
        i = 1
        while len(videos) < target_count:

            if i % 5 == 0:
                # each video is 168px
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(4)

            try:          
                video_selector = f"{parent_css} ytd-compact-video-renderer:nth-of-type({i})"
                video_element = driver.find_element(By.CSS_SELECTOR, video_selector)
                videos.append(video_element)  
            except NoSuchElementException:
                print('no vid')
                break 

            i += 1


        reels = []
        i = 1
        scroll_to_top(driver)

        def scroll_right_reels(driver):
            right_arrow_btn = driver.find_element(By.CSS_SELECTOR, "div#right-arrow.style-scope.yt-horizontal-list-renderer button")
            driver.execute_script("arguments[0].scrollIntoView();", right_arrow_btn)
            jsclick(driver, right_arrow_btn)

        while len(reels) < target_count:
            if i % 3 == 0:
                scroll_right_reels(driver)
                time.sleep(4)

            try:
                reel_selector = f"{parent_css} ytm-shorts-lockup-view-model-v2:nth-of-type({i})"
                reel_element = driver.find_element(By.CSS_SELECTOR, reel_selector)
                reels.append(reel_element)  
            except NoSuchElementException:
                break

            i += 1

        
        return videos, playlists, reels
 

    def parse_video_element(video_element) -> dict:

        thumbnail_elem = video_element.find_element(By.CSS_SELECTOR, "ytd-thumbnail > a")
        video_url = thumbnail_elem.get_attribute("href")
        video_id = parse_video_id(video_url)
        video_title = video_element.find_element(By.CSS_SELECTOR, "span#video-title").get_attribute('title')
        video_thumbnail = video_element.find_element(By.CSS_SELECTOR, "img").get_attribute("src")

        # if not video_thumbnail:
        #     print("i.ytimg.com" in video_element.get_attribute("innerHTML"))

        out = {
            "id": video_id,
            "url": video_url, 
            "title": video_title,
            "thumbnail": video_thumbnail
        }

        return out
    
    def parse_reel_element(reel_element) -> dict:

        reel_url = reel_element.find_element(By.CSS_SELECTOR, "a.shortsLockupViewModelHostEndpoint.reel-item-endpoint").get_attribute('href')
        reel_id = parse_reel_id(reel_url)
        reel_title = reel_element.find_element(By.CSS_SELECTOR, "a.shortsLockupViewModelHostEndpoint.shortsLockupViewModelHostOutsideMetadataEndpoint").get_attribute('title')
        reel_thumbnail = reel_element.find_element(By.CSS_SELECTOR, "img").get_attribute("src")

        out = {
            "id": reel_id,
            "url": reel_url,
            "title": reel_title,
            "thumbnail": reel_thumbnail
        }

        return out

    def parse_playlist_element(playlist_element) -> dict:

        meta_elem = playlist_element.find_element(By.CSS_SELECTOR, "a.yt-lockup-metadata-view-model-wiz__title")
        playlist_url = meta_elem.get_attribute("href")
        playlist_title = meta_elem.find_element(By.CSS_SELECTOR, "span").get_attribute("innerHTML")
        playlist_thumbnail = playlist_element.find_element(By.CSS_SELECTOR, "yt-collection-thumbnail-view-model img").get_attribute("src")

        out = {
            "id": "playlist_id",
            "url": playlist_url,
            "title": playlist_title,
            "thumbnail": playlist_thumbnail
        }
        return out

    # return watch next videos on a particular video/playlist page

    tabs = get_tabs(driver)

    side_ad_img = get_side_ad_img(driver)
    if side_ad_img:
        side_ad_site = get_side_ad_site(driver)
        side_ad_text, side_ad_link = get_side_ad_text_and_link(driver)
    else:
        side_ad_site, side_ad_text, side_ad_link = None, None, None

    videos, playlists, reels = get_upnext_lists(driver, target_count)
    videos = [parse_video_element(elem) for elem in videos]
    reels = [parse_reel_element(elem) for elem in reels]
    playlists = [parse_playlist_element(elem) for elem in playlists]

    video_title = get_video_title(driver)

    output = {
        "video_id": parse_video_id(url),
        "video_url": url,
        "video_title": video_title,
        "is_for_kids": is_for_kids(driver),
        "side_ad": {
            "side_ad_img": side_ad_img,
            "side_ad_site": side_ad_site,
            "side_ad_text": side_ad_text,
            "side_ad_link": side_ad_link
        },
        "tabs": tabs,
        "videos": videos,
        "reels": reels,
        "playlists": playlists
    }


    return output


if __name__ == "__main__":

    # driver = create_driver(headless=False, user_data_dir="C:\\Users\\cmai\\Documents\\UserData_happysquare88")

    is_random_seed = True
    random.seed(23)

    df = pd.read_csv("video_list/ytk_nokids_apr24.csv")
    video_urls = df["video_url"].tolist()

    if is_random_seed:
        random.shuffle(video_urls)


    for url in video_urls:

        driver = create_driver(headless=False)

        curr_video_url = url
        curr_video_id = parse_video_id(curr_video_url)

        timeid = get_timestamp()

        output_dir = f"output_recs/output_{curr_video_id}_{timeid}"
        dirs = ['output_recs', output_dir]
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)

        visited_urls = []
        
        next_video_url = curr_video_url
        prev_video_url = curr_video_url

        for epoch in range(20):
            
            time.sleep(2)
            driver.get(next_video_url)
            time.sleep(5)

            visited_urls.append(next_video_url)

            watch_video(driver, duration=10)
            output = crawl_recommendations(driver, next_video_url, target_count=20)
            output["prev_video_url"] = prev_video_url

            next_video_candidates = output['videos']
            assert(len(next_video_candidates) > 0)

            if is_random_seed:
                random.shuffle(next_video_candidates)

            for i in range(len(next_video_candidates)):
                next_video_url = next_video_candidates[i]['url']
                next_video_title = next_video_candidates[i]['title']

                if next_video_url not in visited_urls:
                    break
            
            output["next_video_url"] = next_video_url
            output["next_video_title"] = next_video_title
            prev_video_url = output["video_url"]
            prev_video_id = parse_video_id(prev_video_url)

            scroll_to_top(driver)
            driver.save_screenshot(f"{output_dir}/epoch_{epoch}_{prev_video_id}_screenshot.png")

            with open(f"{output_dir}/epoch_{epoch}_{prev_video_id}.json", "w", encoding="utf-8") as json_file:
                json.dump(output, json_file, indent=4) 

        driver.quit()

        
