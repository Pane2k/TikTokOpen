import asyncio
from TikTok.Statistic.tiktok import tiktokUserCountVideoViews, SameMsTokenException
from TikTok.Statistic.SingleUser import users_videos_with_hashtag
from TikTok.Cookies.cookie import getMsToken, readOldMsToken, saveMsToken, get_tiktok_cookies_from_file,getCookiesFromFile
from TikTok.Server.users import get_user_list
import time
import os
import json

def getNewMsToken():
    try:
        
        
        ms_token = get_tiktok_cookies_from_file("cookies.txt")
        print(f" ms_token:\t {ms_token} \n")
        
        
        return ms_token
    
    except Exception as e:
        print("Exception" + e)
    except SameMsTokenException as e:
        print(e.message)
    except ValueError as e:
        print(e)
        print("Please check your ms_token")
    

def getUserList(userlistLink: str):
    userlist = get_user_list(userlistLink)
    if not userlist:
        raise Exception("No users found in the user list.")
    return userlist

async def divide_list(userlist: list, num_parts: int, selectedPart: int) -> list:
    userlist = userlist[selectedPart::num_parts]
    return userlist

def saveIndex(index: dict):
    with open("Data/JSON/index.json", "w") as f:
        json.dump(index, f)
def openIndex() -> tuple:
    with open("Data/JSON/index.json", "r") as f:
        index = f.read()
    index = json.loads(index)
    
    return index["parts"], index["selectedPart"]
            
async def getInfo(hashtag: str, userlistLink: str) -> dict:
    
    # ms_token = get_tiktok_cookies_from_file("Data/JSON/cookies.json")
    userlist = getUserList(userlistLink)
    {
    # length = len(userlist)
    # try:
    #     num_parts, selectedPart = openIndex()
    #     print(f"num_parts: {num_parts}, selectedPart: {selectedPart}")
    # except:   
    #     print("No index.json")
    #     num_parts = 1
    #     selectedPart = 0
        
    # if selectedPart >= num_parts -1:
    #     selectedPart = 0
    # else:
    #     selectedPart += 1
    
    # maxusersinrow = 16
    # num_parts = length // maxusersinrow
    
    # if num_parts == 0:
    #     num_parts = 1
    # print(f"num_parts: {num_parts}, selectedPart: {selectedPart}")
    
    # userSmallLists = await divide_list(userlist, num_parts, selectedPart)
    # print(f"userSmallLists: {userSmallLists}")
    # userlist = userSmallLists
    
    # saveIndex({"parts": num_parts, "selectedPart": selectedPart})
    }
    blackList=getBlackList("Data/JSON/blackList.json")
    
    result = await users_videos_with_hashtag(
        usernameList=userlist,
        hashtag=hashtag,
        blackList=blackList
        )
    
    
    return result #result
    
def getBlackList(blackListFile: str) -> dict:
    try:
        with open(blackListFile, "r") as f:
            blackList = f.read()
        if not blackList:
            return {}
        json_blackList = json.loads(blackList)
        return json_blackList
    except Exception as e:
        print(e)
        return {}
#if __name__ == "__main__":
    # ms_token= get_tiktok_cookies_from_file("cookies.txt")
    # userlistLink = "tiktok_stats/tiktokNames.txt"
    # userlistLink = "tiktok_stats/names.txt"
    # userlist = getUserList(userlistLink)
    # hashtag = "костиккакто"
    # result = 0
    # blackList=getBlackList("blackList.json")
    # print(f"userlist = {blackList}, users = {blackList.get('usernames')}, videos = {blackList.get('videos')}")
    
    # try:
    #     result = asyncio.run(tiktokUserCountVideoViews(
    #         userlist=userlist,
    #         ms_token="pLSi7qEbF7imuiF0_ySIDEJe_Ew97wEpGvTZL5Icr8WmcazmH8qwiGigUt7HwWbk6sNffDl6KqnK5Ll1WfqRawl3f-zVNtcSD6iAfRL86GzR5z2A7k5O1BrGtsumNbKFy2XuzYca1SAotXiHd16_",
    #         hashtag=hashtag,
    #         blackList=blackList
    #         ))
    # except SameMsTokenException as e:
    #     print(e.message)
        
    # print(f"returnValue = {result}")
    #asyncio.run(getInfo("костиккакто", "tiktok_stats/tiktokNames.txt"))
