import configparser
import sys
import time

import bs4
import PySimpleGUI
import requests

config = configparser.ConfigParser()
config.read("settings.ini", "utf_8")

wait_time = config.getint("General", "ScrapingWaitTime")
user_agent = config["General"]["ScrapingUserAgent"]


# requests.getのUA偽装
def get_fakeua(url):
    time.sleep(wait_time)
    return requests.get(url, headers={"User-Agent": user_agent})


# スクリプト出没スレを読み込む
def read_thread_list():
    with open("script-threadkeys.txt", encoding="utf_8") as file:
        return [x.split(" ")[0] for x in file.read().splitlines()]


# スクリプトと思われるレスを取得
def get_script_res(thread_list):
    res_list = []
    for thread in thread_list:
        thread_request = get_fakeua(
            "https://swallow.5ch.net/test/read.cgi/livejupiter/" + thread + "/"
        )
        if thread_request.status_code == requests.codes.gone:
            input("GONE規制に引っかかったと思われます。ScrapingWaitTimeを調整してください。ENTERキーで終了します。")
            sys.exit()
        thread_soup = bs4.BeautifulSoup(
            thread_request.content,
            "html.parser",
        )
        res_list.extend(
            x.text.strip()
            for x in thread_soup.find_all("span", class_="escaped")
            if x.find("a", class_="reply_link")
        )
    return res_list


# GUIを作成してスクリプトではないレスを選択
def create_selector_gui(res_list):
    window = PySimpleGUI.Window(
        "NanJ Script Regex Helper",
        [
            [
                PySimpleGUI.Listbox(
                    res_list,
                    size=(100, 30),
                    select_mode=PySimpleGUI.LISTBOX_SELECT_MODE_MULTIPLE,
                    key="selector",
                )
            ],
            [PySimpleGUI.Button("OK")],
        ],
        element_justification="c",
    )
    delete_res_list = []
    while True:
        event, values = window.read()
        if event == PySimpleGUI.WIN_CLOSED:
            break
        elif event == "OK":
            popup = PySimpleGUI.Window(
                "確認",
                [
                    [PySimpleGUI.Text("以下のレスを除外してレス一覧を生成しますか？")],
                    [
                        PySimpleGUI.Listbox(
                            values["selector"],
                            size=(80, 25),
                            select_mode=PySimpleGUI.LISTBOX_SELECT_MODE_BROWSE,
                        )
                    ],
                    [PySimpleGUI.Button("OK"), PySimpleGUI.Button("キャンセル")],
                ],
                element_justification="c",
                modal=True,
            )
            exit_code = 0
            while True:
                popup_event, popup_values = popup.read()
                if popup_event == PySimpleGUI.WIN_CLOSED or popup_event == "キャンセル":
                    break
                elif popup_event == "OK":
                    delete_res_list.extend(
                        window.Element("selector").Widget.curselection()
                    )
                    exit_code = 1
                    break
            popup.close()
            if exit_code:
                break
            else:
                continue
    window.close()
    return delete_res_list


# スクリプトではないレスを削除
def delete_not_script_res(res_list, delete_res_list):
    for index, res in list(enumerate(res_list))[::-1]:
        if index in delete_res_list:
            del res_list[index]


# 結果を書き込む
def write_res_list(res_list):
    with open("script-res-db.txt", "w", encoding="utf_8") as file:
        file.write("\n".join(res_list))


thread_list = read_thread_list()
script_res_list = get_script_res(thread_list)
delete_res_list = create_selector_gui(script_res_list)
delete_not_script_res(script_res_list, delete_res_list)
write_res_list(script_res_list)
