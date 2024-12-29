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
import os
import random
import math
# Replace with your actual function to get TikTok data


def get_tiktok_data(hashtag="костиккакто", userlistLink="Data/TXT/Cacto0o.txt") -> dict:
    try:
        return getInfo(hashtag, userlistLink)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching TikTok data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


# Global variables (better to use a class)
startTime = 1734648586
donateAddTime = 35497352
endTime = startTime + donateAddTime
data_dict = None
global lastReloadTime
global doUpdating
lastReloadTime = time.time()


def save_data(data):
    if not os.path.exists("Data/JSON/"):
        os.makedirs("Data/JSON/")
    if type(data) == str:
        json_acceptable_string = data.replace("'", "\"")
        data = json.loads(json_acceptable_string)

    with open("Data/JSON/data.json", "r") as f:
        data_dict = json.loads(f.read())
    for user_data in data["userStats"]:
        if user_data == 0:
            continue
        for new_user_data in data_dict["userStats"]:
            if new_user_data == 0:
                continue
            if (user_data["username"] == new_user_data["username"]):
                user_data["total_views"] = new_user_data["total_views"]
                user_data["total_videos_with_tag"] = new_user_data["total_videos_with_tag"]
                print(f"Updated user: {user_data['username']}")
                break
        else:

            data_dict.get("userStats").append(user_data)
            print(f"newUser {user_data['username']}")

    with open("Data/JSON/dataNew.json", "w") as f:
        f.write(json.dumps(data_dict))


def open_dataDict() -> dict:
    with open("Data/JSON/TotalView.json", "r") as f:
        data = f.read()
    return json.loads(data)


async def send_data_to_websocket(websocket):
    global data_dict
    global lastReloadTime
    while True:
        data_dict = open_dataDict()
        if data_dict is not None:
            data_dict_a: dict = data_dict
            tiktokTime = startTime + data_dict_a.get('total_total_views', 0)
            time_left = int(tiktokTime - time.time())
            timeToRestart = (lastReloadTime + 300) - time.time()
            transferData = json.dumps({"type": "transfer", "data": {
                                      "time": time_left, "timerToRestart": timeToRestart}})

            try:
                await websocket.send(transferData)
            except websockets.exceptions.ConnectionClosedError:
                print("Websocket connection closed. Exiting send thread.")
                break
        await asyncio.sleep(1)


def fetch_tiktok_data_periodically_main(hashtag="костиккакто"):
    asyncio.run(fetch_tiktok_data_periodically(hashtag))


# 5 minutes
async def fetch_tiktok_data_periodically(hashtag="костиккакто", interval=300):
    global data_dict
    global lastReloadTime
    global doUpdating
    isFirst = True
    while True:
        # print("Starting fetch_tiktok_data_periodically")
        # if isFirst:

        #     isFirst = False
        #     data = getTotalDict()
        #     print(data)
        # else:

        doUpdating = True
        data: dict = await get_tiktok_data(hashtag, userlistLink="Data/TXT/Cacto0o.txt")
        saveTotalViewAndVideos(hashtag)
        data_dict = open_dataDict()
        print(data_dict)

        # if data.get('total_total_views', 0) > 0:
        #     save_data(data)
        doUpdating = False
        lastReloadTime = time.time()
        time.sleep(interval)


def update_data_periodically():
    global data_dict
    print("Starting update_data_periodically")
    hashtag = "костиккакто"
    while True:
        #
        saveTotalViewAndVideos(hashtag)
        data = open_dataDict()
        if data.get('total_views', 0) > 0:
            data_dict = open_dataDict()
        time.sleep(1)


async def handler(websocket):
    global data_dict
    global doUpdating
    while True:
        try:
            data_dict = open_dataDict()
            # Slight delay to avoid immediate re-execution
            if data_dict is not None:
                tiktokTime = startTime + \
                    math.floor(data_dict.get('total_views', 0) / 30000 * 3600)
                time_left = int(tiktokTime - time.time())
                timeToRestart = int((lastReloadTime + 300) - time.time())
                transferData = json.dumps({"type": "transfer", "data": {"time": time_left,
                                                                        "timerToRestart": timeToRestart,
                                                                        "isUpdating": doUpdating
                                                                        }})
                await websocket.send(transferData)
            await asyncio.sleep(1)
        except websockets.exceptions.ConnectionClosedError:
            print("Websocket connection closed.")
            break
        except Exception as e:
            print(f"Error in handler: {e}")
            break


def msTokenFromTiktok():
    asyncio.run(msTokenFromTiktokMain())


async def msTokenFromTiktokMain():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe"
    )
    page = await browser.new_page()
    await page.goto("https://www.tiktok.com/")
    try:
        await asyncio.sleep(2)
        await page.goto("https://www.tiktok.com/")
        while True:
            await asyncio.sleep(random.uniform(0, 2))
            random_number = random.randint(1, 1000)
            if random_number % 2 == 0:
                await page.keyboard.press("L")
            await page.keyboard.press("ArrowDown")
            await asyncio.sleep(random.uniform(0, 2))
            cookies = await page.context.cookies()
            # Save cookies to a file
            with open("Data/JSON/cookies.json", "w") as f:
                json.dump(cookies, f)
            print(get_tiktok_cookies_from_file("Data/JSON/cookies.json"))
            await asyncio.sleep(10)
    except Exception as e:
        print(f"An error occurred: {e}")

    await browser.close()


async def main():
    async with websockets.serve(handler, "localhost", 8001):
        print("Server started on ws://localhost:8001")

        # Start separate thread for fetching data
        threadTikTokInfo = threading.Thread(
            target=fetch_tiktok_data_periodically_main)
        threadTikTokInfo.daemon = True  # Allow the main thread to exit
        threadTikTokInfo.start()

        # threadGettingMsToken  = threading.Thread(target=msTokenFromTiktok)
        # threadGettingMsToken.daemon = True  # Allow the main thread to exit
        # threadGettingMsToken.start()

        threadUpdate = threading.Thread(target=update_data_periodically)
        threadUpdate.daemon = True  # Allow the main thread to exit
        threadUpdate.start()

        await asyncio.Future()  # Keep the event loop running

if __name__ == "__main__":
    asyncio.run(main())
