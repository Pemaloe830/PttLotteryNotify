import threading
import time
import os
import json
from dotenv import load_dotenv
from crawler import *

followSettingFileName = "followSetting.json"

def lineNotifyMessage(token: str, msg: str) -> str:
    headers = {
        "Authorization": "Bearer " + token, 
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    payload = {'message': msg }
    r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
    return r.status_code

def detect(token: str, jsonData: Dict[str, Optional[str]]) -> None:
    try:
        if ("boards" not in jsonData or jsonData["boards"] is None):
            raise Exception("尚未設定欲追蹤的看板資訊")
        period = int(jsonData["detectPeriod_minute"])
        crawler = Crawler(jsonData)
        print('start to crawl')

        while True:
            titleResult, upvoteResult = crawler.Start()
            message = ''
            if titleResult or upvoteResult:
                if titleResult:
                    message += '\n\n【發文】\n' + '\n'.join(titleResult)
                if upvoteResult:
                    message += '\n\n【推文】\n'  + '\n'.join(upvoteResult)
                lineNotifyMessage(token, message)
            time.sleep(period * 60)
    except Exception as e:
            raise e
        
if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("NOTIFY_TOKEN")
    current_project_path = os.getcwd() # 獲取當前專案的路徑（即應用程序運行的目錄）
    jsonFilePath = os.path.join(current_project_path, followSettingFileName)
    if os.path.getsize(jsonFilePath) > 0:
        with open(jsonFilePath, 'r', encoding='utf-8') as file:
            jsonData = json.load(file)
    else:
        raise Exception("json設定檔不可為空白")

    thread = threading.Thread(target=detect, args=(token, jsonData))
    thread.start()