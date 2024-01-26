from board import *
from crawlHelper import *

class Crawler():
    def __init__(self, jsonData: List[Dict[str, Optional[str]]]=None):
        self.crawlBoardList = []
        self.detectPeriodMinute = int(jsonData["detectPeriod_minute"]) if jsonData["detectPeriod_minute"] != None else None
        self.validArticleTime_minute = int(jsonData["validArticleTime_minute"]) if jsonData["validArticleTime_minute"] != None else None
        self.maxTryTimes = int(jsonData["maxTryTimes"]) if jsonData["maxTryTimes"] != None else None
        self.previousCheckingArticle = Article()
        self.AddCrawlBoard(jsonData["boards"])

    def AddCrawlBoard(self, crawlBoardList: List[Dict[str, Optional[str]]]) -> None:
        try:
            if crawlBoardList is None:
                print("未設定任何欲追蹤的看板")
            else:
                #print(crawlBoardList)
                if isinstance(crawlBoardList, list):
                    if len(crawlBoardList) > 0:
                        for board in crawlBoardList:
                            if ("name" in board and board["name"] is not None)\
                                and ("url" in board and board["url"] is not None)\
                                and ("followedAuthors" in board and board["followedAuthors"] is not None)\
                                and ("followedArticleContent" in board and board["followedArticleContent"] is not None)\
                                and ("excludeTitleKeyword" in board and board["excludeTitleKeyword"] is not None):
                                    self.crawlBoardList.append(Board(board["name"], board["url"], board["followedAuthors"], \
                                                                     board["followedArticleContent"], board["excludeTitleKeyword"]))
        except Exception as e:
            raise Exception(f"追蹤看板的設定不符合格式: {e}")

    def Start(self) -> List[str]:
        # 取得並更新文章資訊列表
        titleResult = self.ParsingArticleTitle()
        # 取得文章內文資訊
        upvoteResult = []
        return titleResult, upvoteResult

    def ParsingArticleTitle(self) -> List[str]:
        result = []
        for board in self.crawlBoardList:
            keepPasring = True
            hasUpdateLastArticleUrl = False
            followedAuthorAccountList = [obj.account for obj in board.followedAuthorList]
            #每個週期檢查時，換一次user agent
            userAgent = UserAgent.GetRandomUserAgent()
            url = board.url
            while keepPasring:
                soup = CrawlHelper.GetPageSoupElement(url, userAgent, self.maxTryTimes)
                if soup != None:
                    articles = soup.find_all('div', 'r-ent') # 預設第一個參數為tag名稱，第二個為class名稱
                    if len(articles) > 0:
                        # 從最新的文章(最後的元素)開始判斷
                        for i in range(len(articles)-1, -1, -1): # 每次-1，直到[0]為止
                            if articles[i].find('a'): # 找第一個超連結，有找到表示文章存在，未被刪除
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

                                    date = articles[i].find('div', "date").text.strip()
                                    # 依文章作者，判斷是否需列入提醒項目
                                    author = articles[i].find('div', 'author').text
                                    if author in followedAuthorAccountList:
                                        authorNickname = next((obj.nickname for obj in board.followedAuthorList if obj.account == author), '')
                                        # 設定回傳資訊
                                        result.append(f'【{authorNickname}】 {title}  ({date})')
                                        # 判斷該作者的文章，是否要進一步追蹤內文
                                        isNeedToParsingContent = next((obj.followNewUpvote for obj in board.followedAuthorList if obj.account == author), None)
                                        if isNeedToParsingContent not in (None, False):
                                            # 追蹤文章內文
                                            pass

                                    # 依日期，判斷是否需搜尋上頁的文章
                                    if CrawlHelper.LessThanTwoDay(date):
                                        # 置換下個迴圈的查詢url
                                        url = CrawlHelper.GetPreviousPageUrl(soup)
                                    else:
                                        keepPasring = False
                                        break
        return result
        