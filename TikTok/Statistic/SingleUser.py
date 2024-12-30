from ..TikTokApi import TikTokApi

from ..TikTokApi.api.user import User
from ..TikTokApi.api.video import Video
import asyncio
import os
import json
from datetime import datetime
import math
import random
from tqdm import tqdm
# get your own ms_token from your cookies on tiktok.com
ms_token = os.environ.get("ms_token", None)


def debug(debug: bool = False):
    if debug:
        os.environ["DEBUG"] = "True"
    else:
        os.environ["DEBUG"] = "False"


def openJson(path):
    try:
        with open(path, "r") as f:
            return json.loads(f.read())
    except:
        raise Exception("Error opening json file")


def saveJson(path, data):
    
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(json.dumps(data))


def openTxt(path):
    try:
        with open(path, "r") as f:
            return f.read().splitlines()
    except:
        raise Exception("Error opening txt file")



def saveTxt(path, data):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "w") as f:
        f.write("\n".join(data))


def saveUserInfoInJson(username, data, hashtag="default"):
    saveJson(f"Data/JSON/Users/{hashtag}/{username}.json", data)


def openUserInfoInJson(username, hashtag="default"):
    try:
        return openJson(f"Data/JSON/Users/{hashtag}/{username}.json")
    except:
        return None


def compareUserDataViewsAndSaveWithMore(user1, user2):
    try:
        if user1["total_views"] > user2["total_views"]:
            return False
        else:
            return True
    except:
        print(f"Error comparing user data ")
        return True


def debugPrint(text):
    #print(f"{datetime.now().strftime('%H:%M:%S.%f')}\t{text}")
    pass


async def users_videos_with_hashtag(usernameList, hashtag, blackList: dict[list] = None, ms_token: str = None):
    '''
    Asynchronous function that retrieves TikTok videos with a specific hashtag for a list of usernames, and saves the user's total views and total videos with the hashtag to a JSON file.

    Parameters:
    - `usernameList`: List of TikTok usernames to retrieve videos for.
    - `hashtag`: Hashtag to search for in the user's videos.
    - `blackList`: (Optional) Dictionary containing lists of usernames and video IDs to skip.
    - `ms_token`: (Optional) TikTok API access token.

    '''
    async with TikTokApi() as api:
        debugPrint("Creating sessions")
        try:
            cookieFormLast: list = [openJson("Data/JSON/cookies.json")]
        except:
            print("No cookies found, creating new sessions")
            cookieFormLast = None

        await api.create_sessions(ms_tokens=[ms_token],
                                    num_sessions=1,
                                    sleep_after=20,
                                    headless=False,
                                    # executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
                                    # browser="firefox",
                                    override_browser_args=[
            "--disable-blink-features=AutomationControlled"],
            cookies=cookieFormLast,
            starting_url="https://www.tiktok.com/@tiltocacto0o"
        )

        debugPrint("Sessions created")
        print(blackList.get("usernames", ""))
        for username in tqdm(usernameList):
            if username in blackList.get("usernames", ""):
                debugPrint(
                    f"Skipping user {username} because it is in the blacklist")
                continue
            debugPrint(f"Getting user {username}")
            debugPrint(f"username = {username}")

            try:

                user: User = api.user(username=username)
                user_data = await user.info()
            except:
                print(f"Error getting user {username}")
                continue

            videosLen = user_data["userInfo"]["stats"]["videoCount"]

            debugPrint(f"videosLen = {videosLen} ")
            total_views = 0
            total_videos_with_tag = 0
            try:
                async for video in user.videos(count=videosLen):
                    if video.id in blackList.get("videos", []):
                        continue
                    video: Video

                    play_count = int(video.stats.get("playCount", 0))
                    if any(str(h.name).lower() == hashtag for h in video.hashtags):
                        total_views += play_count
                        total_videos_with_tag += 1
                debugPrint(f"save {username} {total_views}")
                openUserInfoInJson(username=username, hashtag=hashtag)
                if compareUserDataViewsAndSaveWithMore(
                    openUserInfoInJson(username=username,
                                        hashtag=hashtag),
                    {"username": username,
                    "total_views": total_views,
                    "total_videos_with_tag": total_videos_with_tag}
                    ):
                        saveUserInfoInJson(username=username,
                                        data={
                                            "username": username, "total_views": total_views, "total_videos_with_tag": total_videos_with_tag},
                                        hashtag=hashtag)
                else:
                    print(f"skip {username} {total_views}")
            except Exception as e:
                print(f"Error getting videos for user {username}")
                print(e)
                continue
            await asyncio.sleep(random.uniform(0.5, 1.5))
        debugPrint("Closing sessions")
        cookietosave = await api.get_session_cookies(api.sessions[0])
        saveJson("Data/JSON/cookies.json", cookietosave)
        await api.close_sessions()
        await api.stop_playwright()

if __name__ == "__main__":
    os.environ["DEBUG"] = "True"
    # print(os.environ.pop("DEBUG", False))
    usernameList = openTxt("Data/TXT/cacto0o.txt")
    hashtag = "костиккакто"
    blackList = openJson("Data/JSON/blackList.json")
    asyncio.run(users_videos_with_hashtag(
        usernameList=usernameList, hashtag=hashtag, blackList=blackList))
