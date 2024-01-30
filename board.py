from datetime import datetime
from typing import List, Dict, Optional

class Board():
    def __init__(self, name: str, url: str, followedAuthorList: List[Dict[str, Optional[str]]], \
                 followedArticleContent: Dict[str, List[str]], excludeTitleKeywordList: List[str], \
                 notifyContentKeyword: List[str]):
        self.name = name
        self.url = url
        self.followedAuthorList = []
        self.followedContentKeywordList = []
        self.excludeTitleKeywordList = excludeTitleKeywordList
        self.notifyContentKeyword = notifyContentKeyword
        self.lastParsingArticleUrl = None
        self.AddFollowedAuthors(followedAuthorList)
        self.AddFollowedArticleContent(followedArticleContent)
    
    def AddFollowedAuthors(self, followedAuthorList: List[Dict[str, Optional[str]]]) -> None:
        try:
            if followedAuthorList is not None:
                if isinstance(followedAuthorList, list):
                    if len(followedAuthorList) > 0:
                        for author in followedAuthorList:
                            if ("account" in author and author["account"] is not None)\
                                and ("nickname" in author)\
                                and ("followNewArticle" in author and author["followNewArticle"] is not None)\
                                and ("followNewUpvote" in author and author["followNewUpvote"] is not None):
                                    nickname = author["nickname"].strip() if isinstance(author["nickname"], str) else ""
                                    self.followedAuthorList.append(Author(author["account"], nickname, author["followNewArticle"], author["followNewUpvote"]))
        except Exception as e:
            raise Exception(f"追蹤作者的設定不符合格式: {e}")

    def AddFollowedArticleContent(self, followedArticleContent: Dict[str, List[str]]) -> None:
        try:
            if followedArticleContent is not None:
                if isinstance(followedArticleContent, dict):
                    if ("titleInclude" in followedArticleContent and followedArticleContent["titleInclude"] is not None):
                        self.followedContentKeywordList = followedArticleContent["titleInclude"]
        except Exception as e:
            raise Exception(f"追蹤文章內容之關鍵字的設定不符合格式: {e}")

class Author():
    def __init__(self, account: str, nickname: str, followNewArticle: bool, followNewUpvote: bool):
        self.account = account
        self.nickname = nickname
        self.followNewArticle = followNewArticle
        self.followNewUpvote = followNewUpvote

class Article():
    def __init__(self):
        self.url = ''
        self.author = ''
        self.title = ''
        self.postDatetime = None
        self.isNeedToFollow = False
    
    def SetPostTime(self, datetimeStr: datetime):
        self.postDatetime = datetime.strptime(datetimeStr, "%a %b %d %H:%M:%S %Y")

class Upvote():
    def __init__(self, title: str = '', text: str = ''):
        self.articleTitle = title
        self.text = text
        