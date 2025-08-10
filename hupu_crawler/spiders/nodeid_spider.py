import json
from urllib.parse import urlencode
import scrapy


class NodeIDSpider(scrapy.Spider):
    name = "nodeid"
    allowed_domains = ["games.mobileapi.hupu.com"]
    count = 0
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0,
        "AUTOTHROTTLE_ENABLED": False,
    }

    def __init__(self, min_id=0, max_id=6000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_id = int(min_id)
        self.max_id = int(max_id)
        # NBA team names in Chinese
        self.nba_teams = {
            "湖人", "勇士", "凯尔特人", "热火", "公牛", "掘金", "篮网", "快船",
            "太阳", "雄鹿", "步行者", "独行侠", "爵士", "火箭", "奇才", "老鹰",
            "雷霆", "魔术", "黄蜂", "鹈鹕", "开拓者", "马刺", "76人", "猛龙",
            "国王", "灰熊"
        }
        self.base_url = (
            "https://games.mobileapi.hupu.com/1/8.0.99/"
            "bplcommentapi/bpl/score_tree/getSubGroups"
        )

    def start_requests(self):
        """
        Generate one request per outBizNo in the configured range.
        """
        for outBizNo in range(self.min_id, self.max_id + 1):
            qs = urlencode({
                "outBizNo": outBizNo,
                "outBizType": "basketball_match"
            })
            url = f"{self.base_url}?{qs}"
            # dont_filter=True so Scrapy won't skip duplicate URLs
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                cb_kwargs={"outBizNo": outBizNo},
                dont_filter=True
            )

    def parse(self, response, outBizNo):
        """
        Parse the JSON response, filter NBA teams, and yield items.
        """
        try:
            payload = json.loads(response.text)
        except json.JSONDecodeError:
            return

        for group in payload.get("data", []):
            name = group.get("groupName")
            if name in self.nba_teams:
                self.count += 1
                root_id = group.get("rootNodeId")
                # yield a dict; Scrapy will collect these as items
                yield {
                    "outBizNo": outBizNo,
                    "groupName": name,
                    "rootNodeId": root_id
                }

    def closed(self, reason):
        print(f"number of matches: {self.count}")
