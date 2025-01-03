
import json

def getMsToken():
    cookie_keys = ["msToken"]
    json_cookies = get_tiktok_cookies(cookie_keys)
    if json_cookies["found"]:
        ms_token = json_cookies["cookies"]["msToken"]
        #print(ms_token)
    else:
        raise Exception("Missing cookie msToken. Login to your tiktok account and retry")
    saveMsToken(ms_token)
    return ms_token

def saveMsToken(ms_token):
    with open("Data/TXT/Data/ms_token.txt", "w") as f:
        f.write(ms_token)
def readOldMsToken():
    with open("Data/TXT/Data/ms_token.txt", "r") as f:
        ms_token = f.read()
    return ms_token

def get_tiktok_cookies(cookie_keys):
    # Try to get cookie from browser
    ref = ["chromium", "opera", "edge", "firefox", "chrome", "brave"]
    index = 0
    json_cookie = {}
    found = False
    for cookie_fn in [
        ""
    ]:
        try:
            for cookie in cookie_fn(domain_name="tiktok.com"):
                
                if ('tiktok.com' in cookie.domain):

                    # print(f"COOKIE - {ref[index]}: {cookie}")
                    if (cookie.name in cookie_keys):
                        json_cookie['browser'] = ref[index]
                        json_cookie[cookie.name] = cookie.value
                        json_cookie[cookie.name + '_expires'] = cookie.expires

                # Check
                found = True
                for key in cookie_keys:
                    if (json_cookie.get(key, "") == ""):
                        found = False
                        break

        except Exception as e:
            print(e)

        index += 1

        if (found):
            break
    #print("found " + str(found))
    return {"found": found, "cookies": json_cookie}



def get_tiktok_cookies_from_file(filepath: str):
    msToken = ""
    cookies = {}
    with open(filepath, "r") as f:
        cookies = f.read()
    
    cookies = json.loads(cookies)
    
    for cookie in cookies:
        cookie: dict
        if cookie.get("name", "") == "msToken" and cookie.get("domain", "") == ".tiktok.com":
            msToken = cookie.get("value", "")
            break
    
        
    if msToken is None:
        raise Exception("Missing cookie msToken. Login to your tiktok account and retry")
    saveMsToken(msToken)
    return msToken
    
def getCookiesFromFile(filepath: str):
    cookies = {}
    with open(filepath, "r") as f:
        cookies = f.read()

    cookies = json.loads(cookies)
    return cookies
if __name__ == "__main__":
    print(get_tiktok_cookies_from_file())
    