#!/usr/local/bin/python3

from datetime import datetime, timezone
import os
import requests
from PIL import Image
from io import BytesIO
import random
import json
import re
import matplotlib.pyplot as plt
import pickle
import sys

pwd = os.path.dirname(os.path.realpath(__file__))
COOKIE_PATH = os.path.join(pwd, "sl_cookies.pkl")

LOGIN_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Referer":"https://weibo.com/",
    "Sec-Fetch-Dest": "script",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:109.0) Gecko/20100101 Firefox/113.0",
}

DM_HEADERS =  {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Referer":"https://api.weibo.com/chat",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:109.0) Gecko/20100101 Firefox/113.0",
}

def timestamp_ms():
    return str(1000*datetime.now(timezone.utc).timestamp())

def display_msg(msg):
    print(f"\n{msg:.>50}")

def display_session_cookies(s):
    display_msg("print cookies")
    for x in s.cookies:
        print(x)

class WeiboLoginBot:
    def __init__(self):
        self._session = requests.Session()

    def login(self):
        self.get_qrcode()
        self.scan_qrcode()
        self.sso_login()
    
    def save_cookies(self):
        pickle.dump(self._session.cookies, open(COOKIE_PATH, "wb"))

    def get_qrcode(self):
        url = "https://login.sina.com.cn/sso/qrcode/image"
        
        headers = {
        "Host": "login.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:109.0) Gecko/20100101 Firefox/113.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://weibo.com/",
        "Sec-Fetch-Dest": "script",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
        }

        form = {
            "entry": "miniblog",
            "size": "180",
        }

        self._num = random.randint(0,999)
        form["callback"]="STK_" + timestamp_ms() + f"{self._num:0>3}"

        display_msg("get qrcode")
        r = self._session.get(url=url, headers=headers, params=form)
        print(r.status_code)

        match = re.search(r'{"retcode.*type=url"}}', r.text)
        response = json.loads(match.group(0))

        url = response['data']['image']
        self._qrid = response['data']['qrid']
        headers = {
            "Host": "v2.qr.weibo.cn",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:109.0) Gecko/20100101 Firefox/113.0",
            "Accept": "image/avif,image/webp,*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://weibo.com/",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "TE": "trailers",    
        }
        display_msg("get qrcode image")
        r = self._session.get(url=url, headers=headers)
        print(r.status_code)
        image = Image.open(BytesIO(r.content))
        plt.imshow(image)
        plt.title("please scan the code to login")
        plt.show()


    def scan_qrcode(self):
        url = "https://login.sina.com.cn/sso/qrcode/check"

        form = {
            "entry":"miniblog",
            "qrid": self._qrid,
            "callback":"STK_" + timestamp_ms() + f"{self._num:0>3}"
        }

        display_msg("qrcode check")
        r = self._session.get(url=url, headers=LOGIN_HEADERS,params=form)
        print(r.status_code)
        print(r.text)
        match = re.search(r'{"retcode.*"}}', r.text)
        response = json.loads(match.group(0))
        self._alt = response["data"]["alt"]
        print(self._alt)

    def sso_login(self):
        url = "https://login.sina.com.cn/sso/login.php"
        form = {
            "entry": "miniblog",
            "returntype": "TEXT",
            "crossdomain": "1",
            "cdult": "3",
            "domain": "weibo.com",
            "alt": self._alt,
            "savestate": "30",
            "callback":"STK_" + timestamp_ms() + f"{self._num:0>3}",
        }

        display_msg("sso login")
        r = self._session.get(url=url, headers=LOGIN_HEADERS,params=form)
        print(r.status_code)
        match = re.search(r'{"retcode.*"]}', r.text)
        response = json.loads(match.group(0))
        print(response)
        uid = response["uid"]

        url1 = response["crossDomainUrlList"][0]
        url2 = response["crossDomainUrlList"][1]
        url3 = response["crossDomainUrlList"][2]

        form = {
            "action": "login",
            "callback": "STK_" + timestamp_ms() + f"{self._num:0>3}",
        }

        display_msg("cross domain url 1")
        r = self._session.get(url=url1, headers=LOGIN_HEADERS,params=form)
        print(r.status_code)
        print(r.text)

        display_msg("cross domain url 2")
        r = self._session.get(url=url2, headers=LOGIN_HEADERS)
        print(r.status_code)
        print(r.text)

        url = "https://passport.weibo.com/wbsso/login"
        form = {
            "action": "login",
            "callback": "STK_" + timestamp_ms() + f"{self._num:0>3}",
        }

        display_msg("cross domain url 3")
        r = self._session.get(url=url3, headers=LOGIN_HEADERS, params=form)
        print(r.status_code)
        match = re.search(r'{"result.*"}}', r.text)
        response = json.loads(match.group(0))
        print(response)

        url = "https://weibo.com"
        r = self._session.get(url=url, headers=LOGIN_HEADERS)
        print(r.status_code)
        print(r.text)

        display_msg("cookies")
        display_session_cookies(self._session)
        self.save_cookies()

class WeiboBot:
    def __init__(self):
        self._session = requests.Session()
        self._contacts = dict()

        try:
            self.load_cookies()
        except:
            display_msg("getting new cookies")
            b = WeiboLoginBot()
            b.login()

            self.load_cookies()

        self.test_login()

    def test_login(self):
        r = self._session.get(url="https://weibo.com", headers=LOGIN_HEADERS)
        if r.status_code!=200:
            print("login fails, please delete the cookie file and retry")

    def load_cookies(self):
        cookies = pickle.load(open(COOKIE_PATH, "rb"))
        self._session.cookies = cookies
        display_msg("load cookies")
        display_session_cookies(self._session)
        
    def id_from_screenname(self, name):
        url = "https://weibo.com/ajax/user/popcard/get"
        headers =  {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Referer":"https://weibo.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:109.0) Gecko/20100101 Firefox/113.0",
            "x-requested-with": "XMLHttpRequest"
        }
        form = {"screen_name":name}
        r = self._session.get(url=url, headers=headers, params=form)
        print(r.status_code)
        response = r.json()
        data = response["data"]
        if "idstr" in data:
            return data["idstr"]
        else:
            print("id not found for the screen name")
            return None

    def get_private_contacts(self):
        url = "https://api.weibo.com/webim/2/direct_messages/contacts.json"
        form = {
            "special_source": "3",
            "add_virtual_user": "3,4",
            "is_include_group": "0",
            "need_back": "0,0",
            "is_include_folder": "1",
            "count": "500", #maximum val: 500
            "source": "209678993", #don't quite understand what it is
            "t": timestamp_ms(),
        }
        r = self._session.get(url=url, headers=DM_HEADERS, params=form)
        print(r.status_code)
        response = r.json()
        contacts = response["contacts"]

        for contact in contacts:
            print(contact["user"])
            #not strangers
            if "idstr" in contact["user"]:
                self._contacts[contact["user"]["idstr"]] = contact["user"]["name"]

    def get_public_contacts(self):
        url = "https://api.weibo.com/webim/2/direct_messages/public/contacts.json"
        #https://api.weibo.com/webim/2/direct_messages/public/contacts.json?count=50&cursor=0&source=209678993&t=1684022783795
        
    def get_conversations_all(self):
        display_msg("save everything in private chat!")
        self.get_private_contacts()
        for contact_id in self._contacts:
            self.get_conversation(uid=contact_id, screen_name=self._contacts[contact_id])

    def get_conversation(self, uid=None, max_count=10**10, screen_name=None):
        url = "https://api.weibo.com/webim/2/direct_messages/conversation.json"
        form = {
            "convert_emoji": "1",
            "count": "200",
            "max_id": "0",
            "uid": uid,
            "is_include_group": "0",
            "from_contacts": "1",
            "source": "209678993",
            "t": timestamp_ms(),
        }
        
        total_count = 0
        saved_msgs = []
        while True:
            if total_count >= max_count:
                break
            r = self._session.get(url=url, headers=DM_HEADERS, params=form)
            print(r.status_code)
            response = r.json()
            dms = response["direct_messages"]
            total_count+=len(dms)
            if len(dms)==0:
                break
            for msg in dms:
                print(msg["created_at"],msg["sender_screen_name"])
                print(msg["text"])
                saved_msgs.append({"created_at":msg["created_at"], "sender_screen_name":msg["sender_screen_name"], "text":msg["text"]})
            print(f"{total_count} messages fetched")
            form["max_id"] = str(int(dms[-1]["mid"])-1)
        
        if screen_name is not None:
            f = open(f"{uid}_{screen_name}.txt","w")
        else:
            f = open(f"{uid}.txt", "w")
        for msg in reversed(saved_msgs):
            f.write(f"{msg['created_at']} {msg['sender_screen_name']}\n")
            f.write(f"{msg['text']}\n")

if __name__ == "__main__":
    b = WeiboBot()
    b.get_conversations_all()