import asyncio
import websockets
import time
import json
import threading
import requests
import datetime
import traceback
from playwright.async_api import async_playwright
from TikTok.Server.main import getInfo
from TikTok.Server.SaveTotalView import saveTotalViewAndVideos, getTotalDict

from TikTok.Cookies.cookie import get_tiktok_cookies_from_file
from TikTok.TikTokApi import TikTokApi
import os
import random
import math
import colorprint as cp
from TikTok.Statistic.tiktok import saveJson
# Replace with your actual function to get TikTok data

async def getOriginalViews(api: TikTokApi, hashtag):
    tag =  api.hashtag(name=hashtag)
    hashtag_data = await tag.info()

    videoCount = hashtag_data['challengeInfo']['statsV2']['videoCount']
    viewCount  = hashtag_data['challengeInfo']['statsV2']['viewCount']

    saveJson("Data/JSON/RawHashtagStats.json", {"videoCount": videoCount,
                                            "viewCount": viewCount})
    # print("getOriginalViews done")

def get_tiktok_data(hashtag="костиккакто", userlistLink="Data/TXT/Cacto0o.txt") -> dict:
    try:
        return getInfo(hashtag, userlistLink)
    except requests.exceptions.RequestException as e:
        print(f"{cp.RED}Error fetching TikTok data: {e}{cp.RESET}")
        return None
    except Exception as e:
        print(f"{cp.RED}An unexpected error occurred: {e}{cp.RESET}")
        return None


# Global variables (better to use a class)
startTime = 1734648586
donateAddTime = 35497352
endTime = startTime + donateAddTime
data_dict = None
global lastReloadTime
global doUpdating
global dataToResive
lastReloadTime = time.time()


def save_data(data):
    if not os.path.exists("Data/JSON/"):
        os.makedirs("Data/JSON/")
    if type(data) == str:
        json_acceptable_string = data.replace("'", '"')
        data = json.loads(json_acceptable_string)

    with open("Data/JSON/data.json", "r") as f:
        data_dict = json.loads(f.read())
    for user_data in data["userStats"]:
        if user_data == 0:
            continue
        for new_user_data in data_dict["userStats"]:
            if new_user_data == 0:
                continue
            if user_data["username"] == new_user_data["username"]:
                user_data["total_views"] = new_user_data["total_views"]
                user_data["total_videos_with_tag"] = new_user_data[
                    "total_videos_with_tag"
                ]
                print(f"{cp.BRIGHT_BLUE}Updated user: {user_data['username']}{cp.RESET}")
                break
        else:
            data_dict.get("userStats").append(user_data)
            print(f"{cp.BRIGHT_GREEN}newUser {user_data['username']}{cp.RESET}")

    with open("Data/JSON/dataNew.json", "w") as f:
        f.write(json.dumps(data_dict))


def open_dataDict() -> dict:
    if not os.path.exists(os.path.dirname("Data/JSON/TotalView.json")):
        os.makedirs(os.path.dirname("Data/JSON/TotalView.json"))
    with open("Data/JSON/TotalView.json", "r") as f:
        data = f.read()
    return json.loads(data)


def open_rawDataDict() -> dict:
    if not os.path.exists(os.path.dirname("Data/JSON/RawHashtagStats.json")):
        os.makedirs(os.path.dirname("Data/JSON/RawHashtagStats.json"))
    with open("Data/JSON/RawHashtagStats.json", "r") as f:
        data = f.read()
    return json.loads(data)

def open_resiveDataDict() -> dict:
    if not os.path.exists(os.path.dirname("Data/JSON/DataToResive.json")):
        os.makedirs(os.path.dirname("Data/JSON/DataToResive.json"))
    with open("Data/JSON/DataToResive.json", "r") as f:
        data = f.read()
    return json.loads(data)

def fetch_tiktok_data_periodically_main(hashtag="костиккакто"):
    asyncio.run(fetch_tiktok_data_periodically(hashtag))

async def fetch_tiktok_data_periodically(hashtag="костиккакто", interval=300):
    global data_dict
    global lastReloadTime
    global doUpdating
    global dataToResive
    isFirst = True
    await asyncio.sleep(10)
    while True:
        # print("Starting fetch_tiktok_data_periodically")
        # if isFirst:

        #     isFirst = False
        #     data = getTotalDict()
        #     print(data)
        # else:

        doUpdating = True
        await get_tiktok_data(hashtag, userlistLink="Data/TXT/cacto0o.txt")
        saveTotalViewAndVideos(hashtag)
        data_dict = open_dataDict()

        result = open_rawDataDict()


        lastResult = {
            "videoCount": int(result["videoCount"]) - int(data_dict["total_videos_with_tag"]),
            "viewCount":  int(result["viewCount"])  - int(data_dict["total_views"]),
        }

        saveJson("Data/JSON/DataToResive.json", lastResult)
        dataToResive = lastResult

        # if data.get('total_total_views', 0) > 0:
        #     save_data(data)
        doUpdating = False
        lastReloadTime = time.time()
        time.sleep(interval)


def update_data_periodically():
    global data_dict
    print(f"{cp.LIGHT_GRAY}Starting update_data_periodically{cp.RESET}")
    hashtag = "костиккакто"
    
    while True:
        #
        saveTotalViewAndVideos(hashtag)
        data = open_dataDict()
        if data.get("total_views", 0) > 0:
            data_dict = open_dataDict()
        time.sleep(300)


async def handler(websocket):
    global data_dict
    # global doUpdating
    global dataToResive
    while True:
        try:
            dataToResive = open_resiveDataDict()
            # Slight delay to avoid immediate re-execution
            if dataToResive is not None:

                


                views = dataToResive.get("viewCount", 0)
                videos = dataToResive.get("videoCount", 0)
                timeToRestart = int((lastReloadTime + 300) - time.time())
                transferData = json.dumps(
                    {
                        "type": "transfer",
                        "data": {
                            "views": views,
                            "videos": videos,
                            "timerToRestart": timeToRestart,
                        },
                    }
                )
                await websocket.send(transferData)
            await asyncio.sleep(1)
        except websockets.exceptions.ConnectionClosedError:
            print(f"{cp.DARK_GRAY}Websocket connection closed.{cp.RESET}")
            break
        except Exception as e:
            print(f"{cp.RED}Error in handler: {e}{cp.RESET}")
            break


# def msTokenFromTiktok():
#     asyncio.run(msTokenFromTiktokMain())


# async def msTokenFromTiktokMain():
#     playwright = await async_playwright().start()
#     browser = await playwright.chromium.launch(
#         headless=False,
#         executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe"
#     )
#     page = await browser.new_page()
#     await page.goto("https://www.tiktok.com/")
#     try:
#         await asyncio.sleep(2)
#         await page.goto("https://www.tiktok.com/")
#         while True:
#             await asyncio.sleep(random.uniform(0, 2))
#             random_number = random.randint(1, 1000)
#             if random_number % 2 == 0:
#                 await page.keyboard.press("L")
#             await page.keyboard.press("ArrowDown")
#             await asyncio.sleep(random.uniform(0, 2))
#             cookies = await page.context.cookies()
#             # Save cookies to a file
#             with open("Data/JSON/cookies.json", "w") as f:
#                 json.dump(cookies, f)
#             print(get_tiktok_cookies_from_file("Data/JSON/cookies.json"))
#             await asyncio.sleep(10)
#     except Exception as e:
#         print(f"An error occurred: {e}")

#     await browser.close()
async def getviewsAsync():
    global data_dict
    global dataToResive
   
    while True:
        try: 
            TTapi = TikTokApi(logger_name="Tiktoka.log", logging_level=10)
            async with TTapi as apia:
                await apia.create_sessions(
                                            
                                            num_sessions=1,
                                            sleep_after=10,
                                            headless=False,
                                            # executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
                                            # browser="firefox",
                                            override_browser_args=[
                    "--disable-blink-features=AutomationControlled"],
                    starting_url="https://www.tiktok.com/@pane2kvod"
                )
                
                    
                hashtag = "костиккакто"
                await getOriginalViews(apia, hashtag)


                result = open_rawDataDict()
                

                lastResult = {
                    "videoCount": int(result["videoCount"]) - int(data_dict["total_videos_with_tag"]),
                    "viewCount":  int(result["viewCount"])  - int(data_dict["total_views"]),
                }
                print(f"{cp.GREEN}{lastResult}{cp.RESET}")
                saveJson("Data/JSON/DataToResive.json", lastResult)
                dataToResive = lastResult
                
                
            
                await apia.close_sessions()
                await apia.stop_playwright()
                        
        except Exception as e:
            await apia.close_sessions()
            await apia.stop_playwright()
            print(f"{cp.RED}error in {e}{cp.RESET}")
        await asyncio.sleep(5)


def getviews():
    asyncio.run(getviewsAsync())

async def main():
    async with websockets.serve(handler, "localhost", 8001):
        print(f"{cp.LIGHT_GRAY}Server started on ws://localhost:8001{cp.RESET}")

        # Start separate thread for fetching data

        threadTikTokInfo = threading.Thread(target=fetch_tiktok_data_periodically_main)
        threadTikTokInfo.daemon = True  # Allow the main thread to exit
        threadTikTokInfo.start()

        threadUpdate = threading.Thread(target=update_data_periodically)
        threadUpdate.daemon = True  # Allow the main thread to exit
        threadUpdate.start()
        
        # threadGetViews = threading.Thread(target=getviews)
        # threadGetViews.daemon = True  # Allow the main thread to exit
        # threadGetViews.start()

        await asyncio.Future()  # Keep the event loop running

        # threadGettingMsToken  = threading.Thread(target=msTokenFromTiktok)
        # threadGettingMsToken.daemon = True  # Allow the main thread to exit
        # threadGettingMsToken.start()


if __name__ == "__main__":
    asyncio.run(main())
