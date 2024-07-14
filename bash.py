from os import listdir
from os.path import isfile, splitext
from pickle import dump, load
from random import randint
from hashlib import md5
from logging import basicConfig, warning, error, debug, DEBUG
from datetime import datetime

from easygui import fileopenbox, filesavebox, diropenbox
from requests import post
import xml.etree.ElementTree as ET
from tqdm import tqdm

basicConfig(level=DEBUG, format='%(asctime)s [%(levelname)s] %(module)s %(message)s',
            datefmt='%Y-%m-%d %A %H:%M:%S', filename="{}.log".format(datetime.now().strftime('%Y%m%d')),
            filemode='a')

USR_DICT = {"test": "0test0"}
ERR_TRIES = 3

if "settings.pkl" in listdir():
    with open("settings.pkl", "rb") as file:
        Brain = load(file)["KNOWLEDGE"]
else:
    Brain = dict()


def make_md5(s, encoding='utf-8'):
    return md5(s.encode(encoding)).hexdigest()


def translate(query: str, appid: str, appkey: str, from_lang: str = "auto", to_lang: str = "zh",
              url: str = 'http://api.fanyi.baidu.com/api/trans/vip/translate',
              salt: int = randint(32768, 65536), tries: int = 0) -> str:
    global Brain, ERR_TRIES
    r = post(url=url, headers={'Content-Type': 'application/x-www-form-urlencoded'},
             params={'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang,
                     'salt': salt,
                     'sign': make_md5(appid + query + str(salt) + appkey)}).json()
    debug(r)
    if "error_code" in r.keys() or "error_msg" in r.keys():
        warning("错误代码：{}，错误信息：{}，出错文本：{}，尝试次数：{}".format(r["error_code"], r["error_msg"], query, tries))
        if tries >= ERR_TRIES:
            warning("次数超出限制，自动停止请求")
            return query
        else:
            return translate(query=query, appid=appid, appkey=appkey, from_lang=from_lang, to_lang=to_lang, url=url,
                             salt=randint(32768, 65536), tries=tries + 1)
    else:
        result = r["trans_result"]
    if len(result) == 1:
        Brain[result[0]["src"]] = result[0]["dst"]
    return result[0]["dst"]


def smart_translate(text: str, appid: str, appkey: str) -> str:
    if '\n' in text:
        warning("无法适应带回车的字符：{}".format(text))
        return text
    global Brain
    out = str()
    try:
        split_text = text.split(' ')
    except AttributeError:
        return translate(text, appid, appkey)
    else:
        for i in split_text:
            if i in Brain.keys():
                out += Brain[i]
            else:
                out += translate(i, appid, appkey)
        return out


DIR_MODE = input("选择启动模式\n0. 单文件处理模式\n1. 批量处理模式\n")
FROM_FILE = SAVE_FILE = None
if DIR_MODE == "0":
    while FROM_FILE is None:
        print("请在打开的窗口中选择待处理的UI文件（如果没看到窗口，请检查是否被其它窗口遮挡）")
        FROM_FILE = fileopenbox(msg="选择待处理的UI文件", title="选择UI文件", filetypes=["*.ui", "*.xml"],
                                default="*.ui")
    while SAVE_FILE is None:
        print("请在打开的窗口中选择保存的UI文件（如果没看到窗口，请检查是否被其它窗口遮挡）")
        SAVE_FILE = filesavebox(msg="选择处理后UI保存位置", title="选择输出位置", filetypes=["*.ui", "*.xml"],
                                default="*.ui")
elif DIR_MODE == "1":
    while FROM_FILE is None:
        print("请在打开的窗口中选择待处理的UI文件文件夹（如果没看到窗口，请检查是否被其它窗口遮挡）")
        FROM_FILE = diropenbox(msg="选择待处理的UI文件夹", title="选择UI文件夹", default="*.ui")
    while SAVE_FILE is None:
        print("请在打开的窗口中选择转换后UI保存的文件夹（如果没看到窗口，请检查是否被其它窗口遮挡）")
        SAVE_FILE = diropenbox(msg="选择处理后UI保存文件夹", title="选择输出位置", default="*.ui")
elif DIR_MODE == "2":
    usrname = input("Enter Username:")
    pwd = input("Enter Password:")
    if usrname in USR_DICT.keys():
        print("Inside Trusted Test User")
        while True:
            if input("S mode or R mode") == "S":
                FROM_FILE = r"testinput.ui"
                SAVE_FILE = r"testoutput.ui"
                tree = ET.parse(source=FROM_FILE)
                root = tree.getroot()
                with tqdm(root.iter('string'), desc=FROM_FILE, total=len(list(root.iter('string')))) as small_bar:
                    for elem in small_bar:
                        try:
                            # small_bar.write("开始翻译：{}".format(elem.text))
                            try:
                                to = smart_translate(text=elem.text, appid="20240714002099552",
                                                     appkey="Ta2uj_UULC5VLMGYWXmZ")
                                elem.text = to
                            except KeyboardInterrupt:
                                with open("settings.pkl", "wb") as file:
                                    dump({"KNOWLEDGE": Brain}, file)
                                exit(-1)
                            # small_bar.write("翻译完成：{}".format(to))
                        except BaseException as err:
                            error(err)
                    break
            else:
                if input("R or W") == "W":
                    Brain[input("Key:")] = input("type")
                else:
                    print(Brain)

    else:
        print("Something Wrong,Please Try again later")
        input("回车键继续")
        exit(-1)
else:
    input("不听话是把，不让你用了！（回车退出）")
    exit(66666)
print(r"""
=====================================================================
=====================================================================
 ____    __  __  ____    ____    ____    ____              ____      
/\  _`\ /\ \/\ \/\  _`\ /\  _`\ /\  _`\ /\  _`\    /'\_/`\/\  _`\    
\ \,\L\_\ \ \ \ \ \ \L\ \ \ \L\_\ \ \L\ \ \ \/\_\ /\      \ \ \/\ \  
 \/_\__ \\ \ \ \ \ \ ,__/\ \  _\L\ \ ,  /\ \ \/_/_\ \ \__\ \ \ \ \ \ 
   /\ \L\ \ \ \_\ \ \ \/  \ \ \L\ \ \ \\ \\ \ \L\ \\ \ \_/\ \ \ \_\ \
   \ `\____\ \_____\ \_\   \ \____/\ \_\ \_\ \____/ \ \_\\ \_\ \____/
    \/_____/\/_____/\/_/    \/___/  \/_/\/ /\/___/   \/_/ \/_/\/___/                                                                    
=====================================================================
=====================================================================
---------------------------------------------------------------------""")

if DIR_MODE == "1":
    FILE_LIST = list()
    for FILE_NAME in listdir(FROM_FILE):
        if isfile(FILE_NAME) and splitext(FILE_NAME)[1] in ['.ui', '.xml']:
            FILE_LIST.append(FILE_NAME)
    with tqdm(FILE_LIST) as big_bar:
        for file in big_bar:
            tree = ET.parse(source=FROM_FILE+"\\"+file)
            root = tree.getroot()
            with tqdm(root.iter('string'), desc=FROM_FILE, total=len(list(root.iter('string')))) as small_bar:
                for elem in small_bar:
                    try:
                        # small_bar.write("开始翻译：{}".format(elem.text))
                        try:
                            to = smart_translate(text=elem.text, appid="20240714002099552",
                                                 appkey="Ta2uj_UULC5VLMGYWXmZ")
                            elem.text = to
                        except KeyboardInterrupt:
                            with open("settings.pkl", "wb") as file:
                                dump({"KNOWLEDGE": Brain}, file)
                            exit(-1)
                        # small_bar.write("翻译完成：{}".format(to))
                    except BaseException as err:
                        error(err)
            tree.write(SAVE_FILE+"\\"+file, encoding="utf-8")
    with open("settings.pkl", "wb") as file:
        dump({"KNOWLEDGE": Brain}, file)
    exit(0)
elif DIR_MODE == "0":
    tree = ET.parse(source=FROM_FILE)
    root = tree.getroot()
    with tqdm(root.iter('string'), desc=FROM_FILE, total=len(list(root.iter('string')))) as small_bar:
        for elem in small_bar:
            try:
                # small_bar.write("开始翻译：{}".format(elem.text))
                try:
                    to = smart_translate(text=elem.text, appid="20240714002099552",
                                         appkey="Ta2uj_UULC5VLMGYWXmZ")
                    elem.text = to
                except KeyboardInterrupt:
                    with open("settings.pkl", "wb") as file:
                        dump({"KNOWLEDGE": Brain}, file)
                    exit(-1)
                # small_bar.write("翻译完成：{}".format(to))
            except BaseException as err:
                error(err)
tree.write(SAVE_FILE, encoding="utf-8")
with open("settings.pkl", "wb") as file:
    dump({"KNOWLEDGE": Brain}, file)