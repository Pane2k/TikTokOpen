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
import logging
from queue import Queue
from tenacity import retry, stop_after_attempt, wait_exponential


class TikTokDataService:
    def __init__(
        self,
        hashtag="cacto0oбесконечныйстрим",
        userlist_link="Data/TXT/Cacto0o.txt",
        websocket_host="0.0.0.0",
        websocket_port=8001,
        refresh_interval=60,
    ):
        self.hashtag = hashtag
        self.userlist_link = userlist_link
        self.websocket_host = websocket_host
        self.websocket_port = websocket_port
        self.refresh_interval = refresh_interval
        self.data = {}
        self.last_reload_time = time.time()
        self.data_queue = Queue()
        self.data_to_resive = {}
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if not os.path.exists("Logs/"):
            os.makedirs("Logs/")
        fh = logging.FileHandler("Logs/tiktok_service.log")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        return logger

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _get_tiktok_data(self):
        try:
            data = await getInfo(self.hashtag)
            # self.logger.debug("got TikTok data")
            return data
        except requests.exceptions.RequestException as e:
            self.logger.error(f"{cp.RED}Error fetching TikTok data: {e}{cp.RESET}")
            raise
        except Exception as e:
            self.logger.error(f"{cp.RED}An unexpected error occurred: {e}{cp.RESET}")
            raise

    def _save_data(self, data):
        if not os.path.exists("Data/JSON/"):
            os.makedirs("Data/JSON/")
        if type(data) == str:
            json_acceptable_string = data.replace("'", '"')
            data = json.loads(json_acceptable_string)

        try:
            with open("Data/JSON/data.json", "r") as f:
                data_dict = json.loads(f.read())
        except (FileNotFoundError, json.JSONDecodeError):
            data_dict = {"userStats": []}  # if no file/empty file, create empty dict

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
                    self.logger.debug(
                        f"{cp.BRIGHT_GREEN}Updated user: {user_data['username']}{cp.RESET}"
                    )
                    break
            else:
                data_dict.get("userStats").append(user_data)
                self.logger.info(f"{cp.GREEN}newUser {user_data['username']}{cp.RESET}")

        with open("Data/JSON/dataNew.json", "w") as f:
            json.dump(data_dict, f)

    def _open_dataDict(self) -> dict:
        if not os.path.exists(os.path.dirname("Data/JSON/TotalView.json")):
            os.makedirs(os.path.dirname("Data/JSON/TotalView.json"))
        try:
            with open("Data/JSON/TotalView.json", "r") as f:
                data = f.read()
            return json.loads(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"total_views": 0, "total_videos_with_tag": 0}

    def _open_rawDataDict(self) -> dict:
        if not os.path.exists(os.path.dirname("Data/JSON/RawHashtagStats.json")):
            os.makedirs(os.path.dirname("Data/JSON/RawHashtagStats.json"))
        try:
            with open("Data/JSON/RawHashtagStats.json", "r") as f:
                data = f.read()
            return json.loads(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"videoCount": 0, "viewCount": 0}

    def _open_resiveDataDict(self) -> dict:
        if not os.path.exists(os.path.dirname("Data/JSON/DataToResive.json")):
            os.makedirs(os.path.dirname("Data/JSON/DataToResive.json"))
        try:
            with open("Data/JSON/DataToResive.json", "r") as f:
                data = f.read()
            return json.loads(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"videoCount": 0, "viewCount": 0}

    def _open_blackListInfoDict(self) -> dict:
        if not os.path.exists(os.path.dirname("Data/JSON/blackListStats.json")):
            os.makedirs(os.path.dirname("Data/JSON/blackListStats.json"))
        try:
            with open("Data/JSON/blackListStats.json", "r") as f:
                data = f.read()
            return json.loads(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"videoCount": 0, "viewCount": 0}

    async def _fetch_tiktok_data_periodically(self):
        while True:
            self.logger.debug(
                f"{cp.BRIGHT_MAGENTA}Starting fetch_tiktok_data_periodically{cp.RESET}"
            )

            data = await self._get_tiktok_data()
            saveTotalViewAndVideos(self.hashtag)
            self.data = self._open_dataDict()

            result = self._open_rawDataDict()
            blackListData = self._open_blackListInfoDict()

            lastResult = {
                "videoCount": int(result["videoCount"])
                - int(self.data["total_videos_with_tag"])
                - int(blackListData["blacklistVideos"]),
                "viewCount": int(result["viewCount"])
                - int(self.data["total_views"] - int(blackListData["blacklistViews"])),
            }
            self.logger.info(
                f"{cp.BLUE}{lastResult}{cp.RESET}"
            )
            saveJson("Data/JSON/DataToResive.json", lastResult)
            self.data_to_resive = lastResult

            self.last_reload_time = time.time()
            await asyncio.sleep(self.refresh_interval)

    def _update_data_periodically(self):
        self.logger.info(f"{cp.YELLOW}Starting update_data_periodically{cp.RESET}")

        while True:
            saveTotalViewAndVideos(self.hashtag)
            data = self._open_dataDict()
            if data.get("total_views", 0) > 0:
                self.data = self._open_dataDict()

            time.sleep(self.refresh_interval)

    async def _handler(self, websocket):
        while True:
            try:
                self.data_to_resive = self._open_resiveDataDict()
                if self.data_to_resive is not None:
                    views = self.data_to_resive.get("viewCount", 0)
                    videos = self.data_to_resive.get("videoCount", 0)
                    timeToRestart = int(
                        (self.last_reload_time + self.refresh_interval) - time.time()
                    )
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
                self.logger.debug(
                    f"{cp.DARK_GRAY}Websocket connection closed.{cp.RESET}"
                )
                break
            except Exception as e:
                self.logger.error(f"{cp.RED}Error in handler: {e}{cp.RESET}")
                break

    async def _get_original_views(self, api: TikTokApi, hashtag):
        try:
            tag = api.hashtag(name=hashtag)
            hashtag_data = await tag.info()
            videoCount = hashtag_data["challengeInfo"]["statsV2"]["videoCount"]
            viewCount = hashtag_data["challengeInfo"]["statsV2"]["viewCount"]
            saveJson(
                "Data/JSON/RawHashtagStats.json",
                {"videoCount": videoCount, "viewCount": viewCount},
            )
        except Exception as e:
            self.logger.error(f"{cp.RED}Error getting original views: {e}{cp.RESET}")

    async def _get_views_async(self):
        while True:
            try:
                TTapi = TikTokApi(logger_name="Tiktoka.log", logging_level=10)
                async with TTapi as apia:
                    await apia.create_sessions(
                        num_sessions=1,
                        sleep_after=10,
                        headless=False,
                        override_browser_args=[
                            "--disable-blink-features=AutomationControlled"
                        ],
                        starting_url="https://www.tiktok.com/@pane2kvod",
                    )
                    await self._get_original_views(apia, self.hashtag)
                    result = self._open_rawDataDict()

                    lastResult = {
                        "videoCount": int(result["videoCount"])
                        - int(self.data["total_videos_with_tag"]),
                        "viewCount": int(result["viewCount"])
                        - int(self.data["total_views"]),
                    }
                    self.logger.info(f"{cp.BLUE}lastResult: {lastResult}{cp.RESET}")
                    saveJson("Data/JSON/DataToResive.json", lastResult)
                    self.data_to_resive = lastResult
                    await apia.close_sessions()
                    await apia.stop_playwright()

            except Exception as e:
                self.logger.error(f"{cp.RED}error in _get_views_async {e}{cp.RESET}")
                try:
                    await apia.close_sessions()
                    await apia.stop_playwright()
                except:
                    pass
            await asyncio.sleep(5)

    def _get_views(self):
        asyncio.run(self._get_views_async())

    async def run(self):
        async with websockets.serve(
            self._handler, self.websocket_host, self.websocket_port
        ):
            self.logger.info(
                f"{cp.BRIGHT_CYAN}Server started on ws://{self.websocket_host}:{self.websocket_port}{cp.RESET}"
            )

            # Start threads
            threadTikTokInfo = threading.Thread(
                target=asyncio.run, args=(self._fetch_tiktok_data_periodically(),)
            )
            threadTikTokInfo.daemon = True
            threadTikTokInfo.start()

            threadUpdate = threading.Thread(target=self._update_data_periodically)
            threadUpdate.daemon = True
            threadUpdate.start()

            #   threadGetViews = threading.Thread(target=self._get_views)
            #   threadGetViews.daemon = True
            #   threadGetViews.start()

            await asyncio.Future()


if __name__ == "__main__":
    service = TikTokDataService()
    asyncio.run(service.run())
