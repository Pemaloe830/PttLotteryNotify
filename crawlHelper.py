from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Union
import requests
import time
import random

retryPeriod_second = 5

class UserAgent():
    @staticmethod
    def GetRandomUserAgent() -> str:
        headers = [
             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36',
             'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
             'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36',
             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0',
             'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
             'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582',
             'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.8810.3391 Safari/537.36 Edge/18.14383',
             'Mozilla/5.0 (X11) AppleWebKit/62.41 (KHTML, like Gecko) Edge/17.10859 Safari/452.6',
             'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16.2',
             'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
             'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A',
             'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25',
             'Mozilla/5.0 (X11; U; UNICOS lcLinux; en-US) Gecko/20140730 (KHTML, like Gecko, Safari/419.3) Arora/0.8.0',
        ]
        return random.choice(headers)
    
class CrawlHelper():
    @staticmethod
    def GetPageSoupElement(url: str, userAgent: str, maxTryTimes: int) -> Union[BeautifulSoup, None]:
        for _ in range(maxTryTimes):
            r = requests.get(url = url,
                                headers = {'user-agent': userAgent},
                                cookies = {'over18':'1'}) # 一並將已滿18歲的回答傳給server
            if r.status_code == requests.codes.ok:
                return BeautifulSoup(r.text, 'html.parser') # 把網頁解析html代碼為BeautifulSoup格式
            else:
                time.sleep(retryPeriod_second)
        return None
        

    @staticmethod
    # 找上一頁的url
    def GetPreviousPageUrl(soupElement: BeautifulSoup):
        pageLinks = soupElement.find_all('a', 'btn wide') # 預設第一個參數為tag名稱，第二個為class名稱
        if len(pageLinks) > 0:
            for i in pageLinks:
                if "上頁" in i.text:
                    return f"https://www.ptt.cc{i['href']}"
        return None
    
    @staticmethod
    # 判斷文章是否已發布超過2天
    # (考慮換日問題，以及看板文章列表無標示時分秒的問題，故至多查詢2天內的文章)
    def LessThanTwoDay(inputDate: str) -> bool:
        current_time = datetime.now()
        # 看板文章列表的預設日期格式為: MM/DD
        ## 日期格式化後，預設時分秒皆為0
        formattedInputDate = datetime.strptime(inputDate, "%m/%d")
        # 置換年份 (取代預設的1900年)
        ## 若文章月份大於當前月份，代表跨了一個年度
        if formattedInputDate.month > current_time.month:
            formattedInputDate = formattedInputDate.replace(year=current_time.year - 1)
        else:
            formattedInputDate = formattedInputDate.replace(year=current_time.year)
        
        one_day_ago = current_time - timedelta(days=2)
        if one_day_ago > formattedInputDate:
            return False
        return True
            