from utils import *

import csv
import sys
import logging

logger = logging.getLogger("ytk_logger")
logger.setLevel(logging.DEBUG) 

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def load_script_tag(driver: webdriver.Chrome):
    # loads a web element that contains a lot of useful info
    global SCRIPT_TAG
    try:
        driver_wait(driver, 10, (By.ID, 'microformat'))
        element_text = driver.find_element(By.CSS_SELECTOR, "#microformat script").get_attribute("innerHTML")
        SCRIPT_TAG = json.loads(element_text)
    except TimeoutException:
        SCRIPT_TAG = None

def get_video_title() -> str:
    try:
        title = SCRIPT_TAG['name']
        return title
    except (TypeError, KeyError) as e:
        return None
    

def get_channel_name() -> str:
    try:
        name = SCRIPT_TAG['author']
        return name
    except (TypeError, KeyError) as e:
        return None


def get_video_info(video_id_list: list):

    timestamp = get_timestamp()
    output_file = open(f"ytk_{timestamp}.csv", "w", encoding="utf-8")
    output_writer = csv.writer(output_file,
								delimiter = ",",
								quotechar = '"',
								quoting = csv.QUOTE_MINIMAL,
								lineterminator = "\n")
    
    # output_writer.writerow(['video_id', 'video_url', 'video_title', 'channel_name', 'is_for_kids'])
    output_writer.writerow(['video_id', 'video_url', 'is_for_kids'])

    for index, video_id in enumerate(video_id_list):
        
        driver.get(url(video_id))
        time.sleep(5)
        # load_script_tag(driver)
        # video_title = get_video_title()
        # channel_name = get_channel_name()
        video_is_for_kids = is_for_kids(driver)

        output_writer.writerow([video_id,
                                url(video_id),
                                # video_title,
                                # channel_name,
                                video_is_for_kids])
        
        output_file.flush()
        os.fsync(output_file)
        logger.info(f"{index}: {video_id} - ytk: {video_is_for_kids}")

   

if __name__ == "__main__":

    args = sys.argv[1:]
    if args:
        input_file = args[0]
    else:
        raise RuntimeError('no input file')
    
    headless = boolify(args[1])
    
    driver = create_driver(headless=headless)

    df = pd.read_csv(input_file)
    get_video_info(df["video_id"].tolist())