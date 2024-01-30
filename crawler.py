from board import *
from crawlHelper import *

domainName = 'https://www.ptt.cc'

class Crawler():
    def __init__(self, jsonData: List[Dict[str, Optional[str]]]=None):
        self.crawlBoardList = []
        self.detectContent_articleUrlList = []
        self.detectPeriodMinute = int(jsonData["detectPeriod_minute"]) if jsonData["detectPeriod_minute"] != None else None
        self.validArticleTime_minute = int(jsonData["validArticleTime_minute"]) if jsonData["validArticleTime_minute"] != None else None
        self.maxTryTimes = int(jsonData["maxTryTimes"]) if jsonData["maxTryTimes"] != None else None
        self.previousCheckRecord = {}
        self.AddCrawlBoard(jsonData["boards"])

    def AddCrawlBoard(self, crawlBoardList: List[Dict[str, Optional[str]]]) -> None:
        try:
            if crawlBoardList is None:
                print("未設定任何欲追蹤的看板")
            else:
                if isinstance(crawlBoardList, list):
                    if len(crawlBoardList) > 0:
                        for board in crawlBoardList:
                            if ("name" in board and board["name"] is not None)\
                                and ("url" in board and board["url"] is not None)\
                                and ("followedAuthors" in board and board["followedAuthors"] is not None)\
                                and ("followedArticleContent" in board and board["followedArticleContent"] is not None)\
                                and ("excludeTitleKeyword" in board and board["excludeTitleKeyword"] is not None)\
                                and ("notifyContentKeyword" in board and board["notifyContentKeyword"] is not None):
                                    self.crawlBoardList.append(Board(board["name"], board["url"], board["followedAuthors"], \
                                                                     board["followedArticleContent"], board["excludeTitleKeyword"], board["notifyContentKeyword"]))
        except Exception as e:
            raise Exception(f"追蹤看板的設定不符合格式: {e}")

    def Start(self) -> List[str]:
        # 取得並更新文章資訊列表
        titleResult = self.ParsingArticleTitle()
        # 取得文章內文資訊
        upvoteResult = self.parsingArticleContent()
        return titleResult, upvoteResult

    def ParsingArticleTitle(self) -> List[str]:
        result = []
        for board in self.crawlBoardList:
            keepPasring = True
            hasUpdateLastArticleUrl = False
            followedAuthorAccountList = [obj.account for obj in board.followedAuthorList]
            # 每個週期檢查時，換一次user agent
            userAgent = UserAgent.GetRandomUserAgent()
            articleListUrl = board.url
            while keepPasring:
                articleListSoup = CrawlHelper.GetPageSoupElement(articleListUrl, userAgent, self.maxTryTimes)
                if articleListSoup != None:
                    articles = articleListSoup.find_all('div', 'r-ent') # 預設第一個參數為tag名稱，第二個為class名稱
                    if len(articles) > 0:
                        # 從最新的文章(最後的元素)開始判斷
                        for i in range(len(articles)-1, -1, -1): # 每次-1，直到[0]為止
                            articleUrlElement = articles[i].find('a')
                            if articleUrlElement: # 找第一個超連結，有找到表示文章存在，未被刪除
                                title = articles[i].find('a').text
                                # 依文章標題，排除不須追蹤的文章
                                if (all(word not in title for word in board.excludeTitleKeywordList)):
                                    # 儲存此次搜尋時，最新的文章網址 (因無其他識別元素，故採用網址判斷是否已重複)
                                    if not hasUpdateLastArticleUrl:
                                        # 初次查詢
                                        if board.lastParsingArticleUrl == None:
                                            board.lastParsingArticleUrl = articles[i].find('a').get('href')
                                            hasUpdateLastArticleUrl = True
                                        # 已查詢到前次進度
                                        elif board.lastParsingArticleUrl == articles[i].find('a').get('href'):
                                            hasUpdateLastArticleUrl = True
                                            keepPasring = False
                                            break

                                    date = articles[i].find('div', 'date').text.strip()
                                    # 依文章作者，判斷是否需列入提醒項目
                                    author = articles[i].find('div', 'author').text
                                    if author in followedAuthorAccountList:
                                        authorNickname = next((obj.nickname for obj in board.followedAuthorList if obj.account == author), '')
                                        # 設定回傳資訊
                                        result.append(f'【{authorNickname}】 {title}  ({date})')
                                        
                                    # 若為LIVE文，判斷是否於時效內而決定追蹤與否
                                    needToParsingArticleDatetime = False
                                            
                                    if 'LIVE' in title.upper():
                                        needToParsingArticleDatetime = True
                                    if needToParsingArticleDatetime:
                                        articleSoup = CrawlHelper.GetPageSoupElement(f"{domainName}{articleUrlElement['href']}", userAgent, self.maxTryTimes)
                                        # 因預設賽事開始前半個小時才能開LIVE文，故僅追蹤3小時內的文章
                                        if CrawlHelper.LessThanTargetHours(articleSoup.find_all('span', 'article-meta-value')[-1].text, 3):
                                            self.detectContent_articleUrlList.append(f"{domainName}{articleUrlElement['href']}")

                                    # 依日期，判斷是否需搜尋上頁的文章
                                    # (考慮換日問題，以及看板文章列表無標示時分秒的問題，故至多查詢2天內的文章)
                                    if CrawlHelper.LessThanTargetDay_simpleFormat(date, 2):
                                        # 置換下個迴圈的查詢url
                                        articleListUrl = CrawlHelper.GetPreviousPageUrl(articleListSoup)
                                    else:
                                        keepPasring = False
                                        break
        return result
    
    def parsingArticleContent(self) -> List[str]:
        result = []
        upvoteList = [] # 儲存推文資訊，將同一篇文章進行彙整

        # 每個週期檢查時，換一次user agent
        userAgent = UserAgent.GetRandomUserAgent()
        if self.detectContent_articleUrlList:
            removeList = []
            for url in self.detectContent_articleUrlList:
                hasKeepLastUpvote = False
                articleSoup = CrawlHelper.GetPageSoupElement(url, userAgent, self.maxTryTimes)
                if not CrawlHelper.LessThanTargetHours(articleSoup.find_all('span', 'article-meta-value')[-1].text, 3):
                    removeList.append(url)
                else:
                    # 根據LIVE文的看板名稱，決定不同的跟蹤作者及跟蹤關鍵字等資訊
                    boardName = articleSoup.find_all('span', 'article-meta-value')[1].text
                    boardObject = next((obj for obj in self.crawlBoardList if obj.name == boardName), None)
                    followedAuthorList = [obj.account for obj in boardObject.followedAuthorList if obj.followNewUpvote]
                    notifyKeywordList = next((obj.notifyContentKeyword for obj in self.crawlBoardList if obj.name == boardName), None)
                    title = articleSoup.find_all('span', 'article-meta-value')[2].text
                    previousCheckedText = None

                    # 分析文章推文
                    pushs = articleSoup.select('div.push:not(.center.warning-box)') # 排除警告文件過大的元素
                    if len(pushs) > 0:
                        # 倒著處理，從最新的推文開始判斷
                        # 因可能有同一位User連續推文，因此index會跳躍，故用while去loop
                        index = len(pushs)-1
                        previousPushIndex = -1

                        while index >= 0:
                            pushUserId = pushs[index].find('span', 'f3 hl push-userid').text
                            if pushUserId not in followedAuthorList:
                                index -= 1
                                continue

                            authorNickname = next((obj.nickname for obj in boardObject.followedAuthorList if obj.account == pushUserId), '')
                            timeStr = pushs[index].find('span', 'push-ipdatetime').text[-6:]
                            # 若前幾行皆為同一位User的推文，則將推文合併成一則，再進行判斷
                            previousPushIndex = index
                            previousPushIndex = index
                            while (previousPushIndex-1) >= 0 :
                                if pushUserId == pushs[previousPushIndex-1].find('span', 'f3 hl push-userid').text:
                                    previousPushIndex -= 1
                                else:
                                    break
                            # 將同一位User的推文合併
                            text = ""
                            for j in range(previousPushIndex, index+1):
                                text += pushs[j].find('span', 'f3 push-content').text.replace(': ', '')
                            
                             # 紀錄該文章，前次檢查的最新推文資訊
                            if not hasKeepLastUpvote:
                                articleUid = CrawlHelper.GetArticleUid(url)
                                if articleUid not in self.previousCheckRecord:
                                    self.previousCheckRecord[articleUid] = text
                                else:
                                    previousCheckedText = self.previousCheckRecord[articleUid]
                                    self.previousCheckRecord[articleUid] = text
                                hasKeepLastUpvote = True
                            
                            # 由新至舊，檢查到前次已檢查的內容即可停止
                            if text == previousCheckedText:
                                break

                            # 符合任一關鍵字 or 符合 "XX大/小 OO K"
                            if any(keyword in text for keyword in notifyKeywordList) \
                                or (any(word in text for word in ['大', '小']) and ('K' in text.upper())):
                                msg = f"【{authorNickname}】 {text} -  {timeStr}"
                                upvoteList.append(Upvote(title, msg))

                            index = previousPushIndex - 1 # 跳過前述同ID的推文

            # 移除超過時效的LIVE文資訊
            # (全部分析完再一起移除，避免在loop中更動到List中的index)
            for url in removeList:
                self.detectContent_articleUrlList.remove(url)
                articleUid = CrawlHelper.GetArticleUid(url)
                if articleUid in self.previousCheckRecord:
                    del self.previousCheckRecord[articleUid]

        # 彙整相同文章的資訊
        upvotes_by_title_dict = {}
        for upvote in upvoteList:
            title = upvote.articleTitle
            if title not in upvotes_by_title_dict:
                upvotes_by_title_dict[title] = []
            upvotes_by_title_dict[title].append(upvote)
        
        notifyMsg = ''
        for title, upvotes in upvotes_by_title_dict.items():
            notifyMsg += (title + '\n')
            for upvote in upvotes:
                notifyMsg += (upvote.text)
            notifyMsg += '\n'
        
        if notifyMsg != '':
            result.append(notifyMsg)

        return result
        