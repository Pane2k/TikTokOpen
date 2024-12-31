import asyncio
import time
import random
from ..TikTokApi import TikTokApi
from ..TikTokApi.exceptions import TikTokException
import json
import os


def saveJson(path, data):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(json.dumps(data))


def saveUserInfoInJson(username, data, hashtag="default"):
    saveJson(f"Data/JSON/Users/{hashtag}/{username}.json", data)


def compareUserDataViewsAndSaveWithMore(user1, user2):
    try:
        if user1["total_views"] > user2["total_views"]:
            return False
        else:
            return True
    except:
        print(f"Error comparing user data ")
        return True


def openUserInfoInJson(username, hashtag="default"):
    try:
        return openJson(f"Data/JSON/Users/{hashtag}/{username}.json")
    except:
        return None


class SameMsTokenException(TikTokException):
    """Raised when the same ms_token is used."""


def openJson(path):
    try:
        with open(path, "r") as f:
            return json.loads(f.read())
    except:
        raise Exception("Error opening json file")


def hashtagProcess(hashtag: str):
    """Converts the given hashtag string to lowercase.

    Parameters:
    - `hashtag: str`: The hashtag string to be processed.

    Returns:
    - `str`: The lowercase version of the input hashtag."""

    hashtag = hashtag.lower()
    return hashtag


async def tiktokUserCountVideoViews(
    usernameList: list = None,
    hashtag: str = None,
    blackList: dict[list] = None,
    ms_token: str = None,
) -> dict:
    """Asynchronous function that retrieves video view counts for a list of TikTok users, filtering by a specified hashtag and blacklist.

    Parameters:
    - `proxylist: list = None`: A list of proxy servers to use.
    - `ms_token: str = None`: A required TikTok MS token.
    - `userlist: list = None`: A list of TikTok usernames to process.
    - `hashtag: str = None`: A hashtag to filter the videos by.
    - `cookies: list[dict] = None`: A list of cookie dictionaries to use for the TikTok API sessions.
    - `blackList: dict[list] = None`: A dictionary containing lists of blacklisted usernames and video IDs.

    Returns:
    - `dict`: A dictionary containing the user statistics and the total number of views across all users."""

    try:
        cookieFormLast: list = [openJson("Data/JSON/cookies.json")]
    except:
        print("No cookies found, creating new sessions")
        cookieFormLast = None

    if not usernameList:
        raise ValueError("A list of users is required.")

    if blackList == None:
        blackList = []
    print(f"username = {blackList}")
    hashtag = hashtagProcess(hashtag)
    print(hashtag)
    for userName in usernameList:
        if userName in blackList:
            usernameList.remove(userName)

    try:
        async with TikTokApi() as api:
            startTime = time.time()
            await api.create_sessions(
                ms_tokens=[ms_token],
                num_sessions=1,
                sleep_after=20,
                headless=False,
                # executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
                # browser="firefox",
                override_browser_args=["--disable-blink-features=AutomationControlled"],
                # cookies=cookieFormLast,
                starting_url="https://www.tiktok.com/@tiltocacto0o",
            )

            tasks = [
                process_user(
                    userName=userName,
                    api=api,
                    hashtag=hashtag,
                    videoBlacklist=blackList.get("videos"),
                    userBlacklist=blackList.get("usernames"),
                )
                for userName in usernameList
            ]
            results = await asyncio.gather(*tasks)
            results = []
            # for userName in usernameList:
            #     print(f"Processing user: {userName}")

            #     results.append(asyncio.gather(process_user(userName=userName,
            #                                                api=api,
            #                                                hashtag=hashtag,
            #                                                videoBlacklist=blackList.get("videos"),
            #                                                userBlacklist=blackList.get("usernames"))))
            total_total_views = 0

            for i in results:
                print(i)
                if isinstance(i, dict):
                    total_total_views += i["total_views"]
                elif isinstance(i, int):
                    total_total_views += i

            results_as_dict = {
                "userStats": results,
                "total_total_views": total_total_views,
            }

            await api.close_sessions()
            endTime = time.time()

            print(
                f"Total views: \033[32m{total_total_views}\033[0m = process time: \033[31m{round(endTime - startTime, 4)}\033[0m"
            )
            return results_as_dict

    except Exception as e:
        if "TimeoutError" in str(e):
            print(f"Error: {e}")
            await api.close_sessions()
            return 0
        else:
            print(f"An error occurred: {type(e).__name__}: {e}")
            await api.close_sessions()
            return 0


async def process_user(
    userName, hashtag: str, api: TikTokApi, userBlacklist, videoBlacklist
):
    """Asynchronously processes a user's TikTok account, retrieving video data and calculating the total views for videos with a specified hashtag.

    Args:
        - `userName (str)`: The username of the TikTok user to process.
        - `hashtag (str)`: The hashtag to search for in the user's videos.
        - `api (TikTokApi)`: The TikTokApi instance to use for making API requests.
        - `userBlacklist (list)`: A list of usernames to exclude from processing.
        - `videoBlacklist (list)`: A list of video IDs to exclude from processing.

    Returns:
        - `dict`: A dictionary containing the username, total views, and total videos with the specified hashtag.
    """
    print(userName)
    # TODO: if user in blacklist then return 0
    # time.sleep(random.randint(1, 5)/10)
    if userName in userBlacklist:
        print(f"{userName} in blacklist")
        return 0
    # await asyncio.sleep(random.randint(1, 5) / 10)
    startTime = time.time()
    try:
        user = api.user(username=userName)

        user_data = await user.info()

        if (
            "userInfo" not in user_data
            or "stats" not in user_data["userInfo"]
            or "videoCount" not in user_data["userInfo"]["stats"]
        ):
            print(f"Error: Invalid user data format for {userName}")
            return 0

        video_count = user_data["userInfo"]["stats"]["videoCount"]
        if video_count == 0:
            print(f"{userName} has no videos.")
            return 0
        print(f"{userName} has {video_count} videos.")

        total_views = 0
        total_videos_with_tag = 0
        blackListI = 0
        try:
            async for video in user.videos(count=video_count):
                if video.id in videoBlacklist:
                    blackListI += 1
                    continue
                try:
                    # TODO: check if video is in a black list
                    play_count = int(
                        video.stats.get("playCount", 0)
                    )  # Handle potential missing data
                    if any(str(h.name).lower() == hashtag for h in video.hashtags):
                        total_views += play_count
                        total_videos_with_tag += 1

                except (KeyError, TypeError, ValueError) as e:
                    print(f"Error processing video for {userName}: {e}")
                    return 0  # Skip to the next video if there's an error

            openUserInfoInJson(username=userName, hashtag=hashtag)
            if compareUserDataViewsAndSaveWithMore(
                openUserInfoInJson(username=userName, hashtag=hashtag),
                {
                    "username": userName,
                    "total_views": total_views,
                    "total_videos_with_tag": total_videos_with_tag,
                },
            ):
                saveUserInfoInJson(
                    username=userName,
                    data={
                        "username": userName,
                        "total_views": total_views,
                        "total_videos_with_tag": total_videos_with_tag,
                    },
                    hashtag=hashtag,
                )
            else:
                print(f"skip {userName} {total_views}")
        except Exception as e:
            print(f"Error getting videos for user {userName}")
            print(e)

        endTime = time.time()
        tabs = ""
        for _ in range(int(24 - len(userName))):
            tabs += " "

        print(
            f"\tTotal views for \033[33m{userName}\033[0m:{tabs} \033[32m{total_views}\033[0m  \ttotal videos with tag: \033[35m{total_videos_with_tag}\033[0m \t total videos: \033[36m{video_count}\033[0m process time: \033[31m{round(endTime - startTime, 4)}\033[0m \tblacklisted: \033[31m{blackListI}\033[0m"
        )
        return {
            "username": userName,
            "total_views": total_views,
            "total_videos_with_tag": total_videos_with_tag,
        }
    except Exception as e:
        print(f"An unexpected error occurred for {userName}: {e}")
        return 0  # Skip to the next video if there's an error
