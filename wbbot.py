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
import copy
import time
from urllib.parse import unquote

import aiohttp
import asyncio

import logging
logger = logging.getLogger(__name__)

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

def reformat_timestamp(x):
    return datetime.strptime(x, "%a %b %d %H:%M:%S %z %Y").strftime('%Y-%m-%d %H:%M:%S %a %z')

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

        headers = copy.deepcopy(LOGIN_HEADERS)
        headers["Host"] = "login.sina.com.cn"
        headers["TE"] = "trailers"
        headers["Connection"] = "keep-alive"

        form = {
            "entry": "miniblog",
            "size": "180",
        }

        self._num = random.randint(0,999)
        form["callback"]="STK_" + timestamp_ms() + f"{self._num:0>3}"

        display_msg("get qrcode")
        r = self._session.get(url=url, headers=headers, params=form)
        logger.debug(r.status_code)

        match = re.search(r'{"retcode.*type=url"}}', r.text)
        response = json.loads(match.group(0))

        url = response['data']['image']
        self._qrid = response['data']['qrid']

        headers = copy.deepcopy(LOGIN_HEADERS)
        headers["Host"] = "v2.qr.weibo.cn"
        headers["TE"] = "trailers"
        headers["Connection"] = "keep-alive"
        headers["Accept"] = "image/avif,image/webp,*/*"
        headers["Sec-Fetch-Dest"] = "image"

        display_msg("get qrcode image")
        r = self._session.get(url=url, headers=headers)
        logger.debug(r.status_code)
        image = Image.open(BytesIO(r.content))
        self._fig = plt.figure(figsize=(2,2))
        self._ax = self._fig.add_subplot()
        self._ax.imshow(image)
        self._ax.set_title("please scan the code to login",fontsize=8)
        plt.show(block=False)
        plt.pause(0.5)

    def scan_qrcode(self):
        qrcode_success = "20000000"
        qrcode_not_scanned = "50114001"
        qrcode_scanned = "50114002"
        qrcode_timeout = "50114003"
        qrcode_exception = "50114015"

        url = "https://login.sina.com.cn/sso/qrcode/check"

        form = {
            "entry":"miniblog",
            "qrid": self._qrid,
            "callback":"STK_" + timestamp_ms() + f"{self._num:0>3}"
        }

        display_msg("qrcode check")
        r = self._session.get(url=url, headers=LOGIN_HEADERS,params=form)
        logger.debug(r.status_code)
        logger.debug(r.text)

        match = re.search(r'"retcode":([0-9]{8})',r.text)
        retcode = match.group(1)

        if retcode == qrcode_success:
            logger.info("qr code scanning success!")
            match = re.search(r'{"retcode.*"}}', r.text)
            response = json.loads(match.group(0))
            self._alt = response["data"]["alt"]
            logger.debug(self._alt)
        elif retcode == qrcode_timeout:
            logger.error("qr code timeout!")
            sys.exit()
        elif retcode == qrcode_exception:
            logger.error("qr code error!")
            sys.exit()
        else:
            if retcode == qrcode_not_scanned:
                logger.error("qr code not scanned!")
            if retcode == qrcode_scanned:
                logger.info("qr code scanned!")
            time.sleep(1)
            self.scan_qrcode()


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
        logger.debug(r.status_code)
        match = re.search(r'{"retcode.*"]}', r.text)
        response = json.loads(match.group(0))
        logger.debug(response)
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
        logger.debug(r.status_code)
        logger.debug(r.text)

        display_msg("cross domain url 2")
        r = self._session.get(url=url2, headers=LOGIN_HEADERS)
        logger.debug(r.status_code)
        logger.debug(r.text)

        url = "https://passport.weibo.com/wbsso/login"
        form = {
            "action": "login",
            "callback": "STK_" + timestamp_ms() + f"{self._num:0>3}",
        }

        display_msg("cross domain url 3")
        r = self._session.get(url=url3, headers=LOGIN_HEADERS, params=form)
        logger.debug(r.status_code)
        match = re.search(r'{"result.*"}}', r.text)
        response = json.loads(match.group(0))
        logger.debug(response)

        url = "https://weibo.com"
        r = self._session.get(url=url, headers=LOGIN_HEADERS)
        logger.debug(r.status_code)
        logger.debug(r.text)

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
            logger.critical("login fails, please delete the cookie file and retry")

    def load_cookies(self):
        cookies = pickle.load(open(COOKIE_PATH, "rb"))
        self._session.cookies = cookies
        display_msg("load cookies")
        display_session_cookies(self._session)

    def id_from_screenname(self, name):
        url = "https://weibo.com/ajax/user/popcard/get"
        headers = copy.deepcopy(DM_HEADERS)
        headers["x-requested-with"] = "XMLHttpRequest"

        form = {"screen_name":name}
        r = self._session.get(url=url, headers=headers, params=form)
        logger.debug(r.status_code)
        response = r.json()
        data = response["data"]
        if "idstr" in data:
            return data["idstr"]
        else:
            logger.info("id not found for the screen name")
            return None

    def _extract_user_from_info(self, uid=None, response=None):
        result = {"uid":uid}
        try:
            user = response['data']['user']
            logger.info(f"{user['id']}, {user['screen_name']}, following: {user['friends_count']}, followers: {user['followers_count']}, status_count: {user['statuses_count']}")
            result["status"]="normal"
            result["user"]=user
            return result
        except:
            logger.debug(uid)
            logger.debug(response)
            result["user"]=None
            logger.debug(f"{response['error_type']}") #link or toast
            if response["error_type"]=="link":
                decoded_url = unquote(response["url"])
                logger.info(decoded_url)
                if "投诉" in decoded_url:
                    result["status"]="banned"
                if "验证" in decoded_url:
                    #该账号内容存在风险，用户验证之前暂时不能查看
                    #该账号行为异常，存在安全风险，用户验证之前暂时不能查看
                    #该账号当前处于异常状态，用户验证之前暂时不能查看
                    result["status"]="risky"
                if "自行" in decoded_url:
                    #该账号因用户自行申请关闭，现已无法查看
                    result["status"]="closed"
            else:
                result["status"]=response["error_type"]
            return result

    def get_profile_info(self, uid):
        """
        Returns: account status and user object
        Even if the account has a custom url, if its status is normal, you should still be able to get the correct information using the numeric id
        """
        url = "https://weibo.com/ajax/profile/info"
        headers = copy.deepcopy(DM_HEADERS)
        headers["x-requested-with"] = "XMLHttpRequest"
        headers["Referer"] = f"https://weibo.com/u/{uid}"

        form = {"uid": str(uid)}
        r = self._session.get(url=url, headers=headers, params=form)
        logger.debug(f"uid-{uid} http status: {r.status_code}")
        response = r.json()
        result = {"uid":uid}
        return self._extract_user_from_info(uid=uid, response=response)

    async def get_profile_info_async(self, session, uid):
        """
        Returns: account status and user object
        Even if the account has a custom url, if its status is normal, you should still be able to get the correct information using the numeric id
        """
        url = "https://weibo.com/ajax/profile/info"
        headers = copy.deepcopy(DM_HEADERS)
        headers["x-requested-with"] = "XMLHttpRequest"
        headers["Referer"] = f"https://weibo.com/u/{uid}"
        form = {"uid": str(uid)}
        try:
            async with session.get(url, headers=headers, params=form) as r:
                response = await r.json()
                logger.debug(f"uid-{uid} http status: {r.status}")
                return self._extract_user_from_info(uid=uid, response=response)
        except:
            return None


    def get_profile_details(self, uid):
        url = "https://weibo.com/ajax/profile/detail"
        headers = copy.deepcopy(DM_HEADERS)
        headers["x-requested-with"] = "XMLHttpRequest"
        headers["Referer"] = f"https://weibo.com/u/{uid}"

        form = {"uid": str(uid)}
        r = self._session.get(url=url, headers=headers, params=form)
        logger.debug(f"uid-{uid} http status: {r.status_code}")
        response = r.json()
        try:
            data = response["data"]
            data["uid"] = uid
            #print(f"{data['sunshine_credit']}, {data['created_at']}")
            return data
        except:
            logger.debug(f"{response['error_type']}")
            return None

    async def get_profile_details_async(self, session, uid):
        url = "https://weibo.com/ajax/profile/detail"
        headers = copy.deepcopy(DM_HEADERS)
        headers["x-requested-with"] = "XMLHttpRequest"
        headers["Referer"] = f"https://weibo.com/u/{uid}"
        form = {"uid": str(uid)}
        try:
            async with session.get(url, headers=headers, params=form) as r:
                response = await r.json()
                logger.debug(f"uid-{uid} http status: {r.status}")
                try:
                    data = response["data"]
                    data["uid"] = uid
                    #print(f"{data['sunshine_credit']}, {data['created_at']}")
                    return data
                except:
                    logger.debug(f"{uid}, {response['error_type']}")
                    return None
        except:
            return None

    def check_muted(self, uid):
        url = "https://weibo.com/ajax/profile/getMuteuser"
        headers = copy.deepcopy(DM_HEADERS)
        headers["x-requested-with"] = "XMLHttpRequest"
        headers["Referer"] = f"https://weibo.com/u/{uid}"
        form = {"uid": str(uid)}

        r = self._session.get(url=url, headers=headers, params=form)
        logger.debug(f"uid-{uid} http status: {r.status_code}")
        try:
            response = r.json()
            logger.debug(response)
            if "data" not in response:
                return "not_existed"
            data = response['data']
            if "text" not in data:
                return "not_muted"
            text = data["text"]
            #因违反社区公约，该用户目前处于禁言状态
            if "处于禁言状态" in text:
                return "temporary_muted"
            #因违反社区公约，该用户处于永久禁言状态
            if "永久禁言" in text:
                return "permanent_muted"
        except:
            return None

    def _get_relationship(self, uid,  url=None, headers=None, form=None, max_count=10**10, location_filter=None, created_since=None, created_before=None):
        page = 0
        total_count = 0 
        while True:
            form['page']=str(page)
            form['uid']=str(uid)
            page+=1
            r = self._session.get(url=url, headers=headers, params=form)
            logger.debug(r.status_code)
            response = r.json()
            users = response["users"]
            total_count+=len(users)
            logger.info(f"{total_count} users fetched")
            for user in users:
                if location_filter is not None and user["location"] != location_filter:
                    continue
                if created_since is not None and datetime.strptime(user["created_at"], "%a %b %d %H:%M:%S %z %Y")<datetime.strptime(created_since, "%Y-%m-%d").replace(tzinfo=timezone.utc):
                    continue
                if created_before is not None and datetime.strptime(user["created_at"], "%a %b %d %H:%M:%S %z %Y")>datetime.strptime(created_before, "%Y-%m-%d").replace(tzinfo=timezone.utc):
                    continue
                #print(user["id"],user["screen_name"], user["created_at"],user["credit_score"],user["urisk"], user["friends_count"], user["followers_count"], user["location"])
                yield user

            if len(users)==0 or total_count>=max_count:
                break

    def get_following(self, uid, max_count = 10**10, location_filter=None, created_since=None, created_before=None):
        url = "https://weibo.com/ajax/friendships/friends"
        headers = copy.deepcopy(DM_HEADERS)
        headers["x-requested-with"] = "XMLHttpRequest"
        headers["Referer"] = f"https://weibo.com/u/page/follow/{uid}"
        form = dict()
        yield from self._get_relationship(uid,  url=url, headers=headers, form=form, max_count=max_count, location_filter=location_filter, created_since=created_since, created_before=created_before)

    def get_followers(self, uid, max_count = 10**10, location_filter=None, created_since=None, created_before=None):
        url = "https://weibo.com/ajax/friendships/friends"
        headers = copy.deepcopy(DM_HEADERS)
        headers["x-requested-with"] = "XMLHttpRequest"
        headers["Referer"] = f"https://weibo.com/u/page/follow/{uid}?relate=fans"
        form = {
            'relate': 'fans',
            'type': 'fans',
            'newFollowerCount': '0'
        }
        yield from self._get_relationship(uid, url=url, headers=headers, form=form, max_count=max_count, location_filter=location_filter, created_since=created_since, created_before=created_before)


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
        logger.debug(r.status_code)
        response = r.json()
        logger.debug(response)
        contacts = response["contacts"]

        for contact in contacts:
            logger.info(f"{contact['user']}")
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
            logger.debug(r.status_code)
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
            f.write(f"{reformat_timestamp(msg['created_at'])} {msg['sender_screen_name']}\n")
            f.write(f"{msg['text']}\n")

if __name__ == "__main__":
    b=WeiboBot()
    b.get_conversations_all()