import json
from pathlib import Path

import scrapy


class MatchSpider(scrapy.Spider):
    name = "match"
    allowed_domains = ["games.mobileapi.hupu.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0,
        "AUTOTHROTTLE_ENABLED": False,
    }

    # Templates for the two JSON endpoints
    STATS_URL = (
        "https://games.mobileapi.hupu.com/1/8.2.99/"
        "bplcommentapi/bff/bpl/score_tree/"
        "groupAndSubNodes?nodeId={rootNodeId}&queryType=hot&page=1&pageSize=20"
    )
    COMMENTS_URL = (
        "https://games.mobileapi.hupu.com/1/8.2.99/"
        "bplcommentapi/bpl/comment/list/"
        "primarySingleRow/hottest?"
        "outBizNo={selfBizId}&outBizType=basketball_item&clientCode="
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node_ids = self.load_node_ids()

    def load_node_ids(self):
        """
        Load node IDs from nba_root_ids.json into a list of dicts:
        [{ outBizNo, groupName, rootNodeId }, ...]
        """
        current_dir = Path(__file__).parent
        project_dir = current_dir.parent.parent
        json_path = project_dir / "nba_root_ids.json"
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.logger.info(f"Loaded {len(data)} node IDs")
            return data
        except Exception as e:
            self.logger.error(f"Could not load node IDs: {e}")
            return []

    def start_requests(self):
        for entry in self.node_ids:
            rid = entry["rootNodeId"]
            url = self.STATS_URL.format(rootNodeId=rid)
            yield scrapy.Request(
                url,
                callback=self.parse_stats,
                cb_kwargs={"entry": entry},
                dont_filter=True,
            )

    def parse_stats(self, response, entry):
        """
        Parse the groupAndSubNodes response to extract each player’s stats,
        then schedule a comment‐fetch for each player.
        """
        try:
            payload = json.loads(response.text)
            nodes = payload["data"]["nodePageResult"]["data"]
        except Exception:
            self.logger.error(f"Bad stats JSON @ {response.url}")
            return

        for section in nodes:
            node = section.get("node", {})
            info = node.get("infoJson", {})
            # ignore referee & coach
            t = info.get("type", [""])[0]
            if t in ("referee", "coach"):
                continue

            # build a partial item
            item = {
                "outBizNo": entry["outBizNo"],
                "team": entry["groupName"],
                "rootNodeId": entry["rootNodeId"],
                "playerName": node.get("name", ""),
                "matchScore": info.get("basketball_match", [""])[0],
                "minutes": info.get("minutes", [""])[0],
                "pts": info.get("pts", [""])[0],
                "ast": info.get("ast", [""])[0],
                "reb": info.get("reb", [""])[0],
                "stl": info.get("stl", [""])[0],
                "blk": info.get("blk", [""])[0],
                "plusMinus": info.get("plusMinus", [""])[0],
            }
            # schedule comments fetch
            biz_id = info.get("selfBizId")
            if biz_id is None:
                # yield with empty comments
                item.update({"comment1": "", "comment2": "", "comment3": ""})
                yield item
            else:
                comments_url = self.COMMENTS_URL.format(selfBizId=biz_id)
                yield scrapy.Request(
                    comments_url,
                    callback=self.parse_comments,
                    cb_kwargs={"item": item},
                    dont_filter=True,
                )

    def parse_comments(self, response, item):
        """
        Parse the hottest comments endpoint, take up to 3, and emit the final item.
        New response format:
        {
          "code": 1,
          "type": "COMMON", 
          "msg": "成功",
          "data": [
            {
              "commentContent": "天赋有限，最后时刻不能指望角色球员来carry。",
              ...
            },
            ...
          ],
          "success": true
        }
        """
        try:
            payload = json.loads(response.text)
            # Check if the response has the expected structure
            if payload.get("success") and "data" in payload:
                comments = payload["data"]
            else:
                # Fallback for old format
                comments = payload.get("data", {}).get("hotCommentModels", [])
        except Exception as e:
            self.logger.error(f"Bad comments JSON @ {response.url}: {e}")
            comments = []

        # Take first 3 commentContent
        for i in range(3):
            key = f"comment{i+1}"
            if i < len(comments):
                # Extract commentContent from the new format and clean for CSV
                comment_content = comments[i].get("commentContent", "")
                item[key] = self.clean_comment_for_csv(comment_content)
            else:
                item[key] = ""
        
        yield item

    def clean_comment_for_csv(self, comment):
        """
        Clean comment text to prevent CSV parsing issues.
        Replaces problematic characters that could break CSV format.
        """
        if not comment:
            return ""
        # Replace commas with semicolons to avoid CSV parsing issues
        # Also handle other potential CSV-breaking characters
        cleaned = comment.replace(",", ";")
        cleaned = cleaned.replace('"', "'")  # Replace double quotes with single quotes
        cleaned = cleaned.replace('\n', ' ')  # Replace newlines with spaces
        cleaned = cleaned.replace('\r', ' ')  # Replace carriage returns with spaces
        return cleaned.strip()