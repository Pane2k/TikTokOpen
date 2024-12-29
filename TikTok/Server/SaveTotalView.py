import json
import os

def saveTotalViewAndVideos(hashtag: str):
    allData = {}
    hashtag = "костиккакто"
    if not os.path.exists(f"Data/JSON/Users/{hashtag}"):
        print('a')
        os.makedirs(f"Data/JSON/Users/{hashtag}")
        
    for user in os.listdir(f"Data/JSON/Users/{hashtag}"):
        if user == "TotalView.json":
            continue
        with open(f"Data/JSON/Users/{hashtag}/{user}", "r") as f:
            allData[user] = json.loads(f.read())
    totalVideos = 0
    totalViews = 0
    for user in allData:
        totalViews += allData[user]["total_views"]
        totalVideos += allData[user]["total_videos_with_tag"]
    dirname = "Data/JSON/TotalView.json"
    if not os.path.exists(os.path.dirname(dirname)):
        os.makedirs(os.path.dirname(dirname))
    
    with open(f"Data/JSON/TotalView.json", "w") as f:
        f.write(json.dumps({
            "total_views": totalViews,
            "total_videos_with_tag": totalVideos
        }))

def getTotalDict() -> dict:
    if os.path.exists(f"Data/JSON/TotalView.json"):
        with open(f"Data/JSON/TotalView.json", "r") as f:
            return json.loads(f.read())
    else:
        return {
            "total_views": 0,
            "total_videos_with_tag": 0
        }
    

if __name__ == "__main__":
    # load all json from Data/JSON/User/{hashtag}/*.json
    
    # save all json to Data/JSON/User/{hashtag}/TotalView.json
    saveTotalViewAndVideos("костиккакто")
    print(getTotalDict())
    
    
        
   
    