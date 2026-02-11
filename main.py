# -*- coding:utf-8 -*-
import datetime

from datetime import datetime
from curl_cffi import requests



class Scraper:
    def __init__(self):
        self.user_id = None
        self.cookies = None
        self.load_info()

    def load_info(self):
        try:
            with open("user_id.ini") as f:
                self.user_id = f.read()
            with open("cookies.ini") as f:
                self.cookies = f.read()
        except Exception as e:
            self.user_id = None
            self.cookies = None

    def request_user_quote(self):
        try:
            url = "https://api.ikuncode.cc/api/user/self"
            headers = {
                "cookie": self.cookies,
                "new-api-user": self.user_id,
                "referer": "https://api.ikuncode.cc/console",
            }
            response = requests.get(url, headers=headers)
            data = response.json()["data"]
            return data
        except Exception as e:
            return None

    def request_user_state(self):
        try:
            end_date = datetime.now()
            start_date = datetime(year=end_date.year, month=end_date.month, day=end_date.day, hour=0, minute=0, second=0)
            url = f"https://api.ikuncode.cc/api/log/self/stat?type=0&token_name=&model_name=&start_timestamp={start_date.timestamp()}&end_timestamp={end_date.timestamp()}&group="
            headers = {
                "cookie": self.cookies,
                "new-api-user": self.user_id,
                "referer": "https://api.ikuncode.cc/console",
            }
            response = requests.get(url, headers=headers)
            data = response.json()["data"]
            return data
        except Exception as e:
            return None

    def quota_to_balance(self, quato):
        return quato * 0.000002


if __name__ == '__main__':
    scraper = Scraper()
    scraper.request_user_state()