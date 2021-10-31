import collections
import configparser
import re
import sys
import time

import bs4
import requests

time_limit = int(input("何時間前までのスレを対象にするか数字を入力してください。（例：24）"))
limit_unixtime = int(time.time()) - time_limit * 3600
config = configparser.ConfigParser()
config.read("settings.ini", "utf_8")

wait_time = config.getint("General", "ScrapingWaitTime")
user_agent = config["General"]["ScrapingUserAgent"]


# requests.getのUA偽装
def get_fakeua(url):
    time.sleep(wait_time)
    return requests.get(url, headers={"User-Agent": user_agent})


# KAKOLOGから直近のスレを取得
def get_recent_threads():
    threadtitle_list = []
    threadkey_list = []
    rescount_list = []

    index = 0
    while True:
        kakolog_soup = bs4.BeautifulSoup(
            get_fakeua(
                "https://swallow.5ch.net/livejupiter/kako/kako"
                + "{:04}".format(index)
                + ".html"
            ).content,
            "html.parser",
        )

        threadkey_list.extend(
            int(x.text.removesuffix(".dat"))
            for x in kakolog_soup.find_all("span", class_="filename")
        )
        threadtitle_list.extend(
            x.text.strip() for x in kakolog_soup.find_all("span", class_="title")
        )
        rescount_list.extend(
            int(x.text) for x in kakolog_soup.find_all("span", class_="lines")
        )

        index += 1
        if threadkey_list[-1] < limit_unixtime:
            break

    return list(zip(threadkey_list, threadtitle_list, rescount_list))


# 完走していないスレ、取得したい時間以外に建てられたスレを除外
def delete_not_require_thread(thread_list):
    for index in [
        i for i, x in enumerate(thread_list) if x[2] < 1002 or x[0] < limit_unixtime
    ][::-1]:
        del thread_list[index]


# スクリプトが出没していないと思われるスレを除外
def delete_not_detect_script_thread(thread_list):
    detect_min_anchor_count = config.getint("Detect", "DetectMinAnchorCount")
    detect_min_script_res = config.getint("Detect", "DetectMinScriptRes")

    for index, thread in list(enumerate(thread_list))[::-1]:
        thread_request = get_fakeua(
            "https://swallow.5ch.net/test/read.cgi/livejupiter/" + str(thread[0]) + "/"
        )
        if thread_request.status_code == requests.codes.gone:
            input("GONE規制に引っかかったと思われます。ScrapingWaitTimeを調整してください。ENTERキーで終了します。")
            sys.exit()
        thread_soup = bs4.BeautifulSoup(
            thread_request.content,
            "html.parser",
        )
        anchor_count_list = [
            int(x.text.removeprefix(">>"))
            for x in thread_soup.find_all("a", class_="reply_link")
            if re.fullmatch(r"\d{1,3}", x.text.removeprefix(">>"))
        ]

        detect_over_count = 0
        for value in collections.Counter(anchor_count_list).values():
            if value > detect_min_anchor_count:
                detect_over_count += 1
        if detect_over_count < detect_min_script_res:
            del thread_list[index]


# 結果を書き込む
def write_thread_list(thread_list):
    with open("script-threadkeys.txt", "w", encoding="utf_8") as file:
        for thread in thread_list:
            file.write(str(thread[0]) + " " + thread[1] + "\n")


recent_thread_list = get_recent_threads()
delete_not_require_thread(recent_thread_list)
delete_not_detect_script_thread(recent_thread_list)
write_thread_list(recent_thread_list)
