from time import sleep
from warnings import catch_warnings, simplefilter
from xml.sax.saxutils import unescape
from random import random
from os import listdir
from os.path import isfile, splitext
from pickle import dump, load

from requests import get
from requests.exceptions import JSONDecodeError
from easygui import fileopenbox, filesavebox, diropenbox
from requests import get
import xml.etree.ElementTree as ET
from tqdm import tqdm


USR_DICT = {"test": "0test0"}

if "settings.pkl" in listdir():
    with open("settings.pkl", "rb") as file:
        PEOPLE_REPAIR = load(file)["PR"]
else:
    PEOPLE_REPAIR = dict()


def translate_num1(text: str, origin_lang: str = "en", output_lang: str = "zh-CN", tries: int = 1) -> str:
    sleep(random()/1.5)
    with catch_warnings():
        simplefilter("ignore")
        output = get("https://translate.appworlds.cn?text={}&from={}&to={}".format(text, origin_lang, output_lang),
                     verify=False).json()
    if output["code"] != 200 and tries < 3:
        sleep(random())
        return translate_num1(text, tries + 1)
    elif output["code"] == 200:
        try:
            return output["data"]
        except AttributeError:
            sleep(random)
            return translate_num1(text, tries + 1)
    else:
        return text


def translate_num2(text: str, tries: int = 1) -> str:
    sleep(random()/1.5)
    try:
        output = get("https://api.52vmy.cn/api/query/fanyi?msg={}".format(text))
        if output.json()["code"] != 200 and tries < 3:
            return translate_num1(text, tries=tries + 1)
        elif output.json()["code"] == 200:
            return output.json()["data"]['target']
        else:
            return text
    except JSONDecodeError:
        return translate_num3(text, tries=tries + 1)
    except AttributeError:
        return translate_num3(text, tries=tries + 1)


def translate_num3(text: str, origin_lang: str = "en", output_lang: str = "zh", tries: int = 1) -> str:
    sleep(random()/1.5)
    with catch_warnings():
        simplefilter("ignore")
        output = get(
            "https://translate.cloudflare.jaxing.cc/?text={}&source_lang={}&target_lang={}".format(text, origin_lang,
                                                                                                   output_lang)).json()
    try:
        if output["code"] != 200 and tries < 3:
            return translate_num1(text, tries=tries + 1)
        elif output["code"] == 200:
            try:
                return output["data"]["response"]["translated_text"]
            except AttributeError:
                return translate_num1(text, tries=tries + 1)
        else:
            return text
    except KeyError:
        return translate_num1(text, tries=tries + 1)


def smart_translate(text: str, repair_dict: dict = {}) -> str:
    global Brain
    out = str()
    try:
        split_text = text.split(' ')
    except AttributeError:
        return translate_num3(text)
    else:
        for i in split_text:
            if i in repair_dict.keys():
                Brain[i] = repair_dict[i]
            if i in Brain.keys():
                out += Brain[i]
            else:
                give = translate_num1(i)
                if i != give:
                    out += give
                else:
                    give = translate_num2(i)
                    if i != give:
                        out += give
                    else:
                        give = translate_num3(i)
                        if i != give:
                            out += give
                        else:
                            return ""
                Brain[i] = give
        return out

Brain = dict()
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
                FROM_FILE = r"D:\cty\python\uihans\testinput.ui"
                SAVE_FILE = r"D:\cty\python\uihans\testoutput.ui"
                tree = ET.parse(source=FROM_FILE)
                root = tree.getroot()
                with tqdm(root.iter('string'), desc=FROM_FILE, total=len(list(root.iter('string')))) as small_bar:
                    for elem in small_bar:
                        # small_bar.write("开始翻译：{}".format(elem.text))
                        try:
                            to = smart_translate(elem.text, PEOPLE_REPAIR)
                            elem.text = to
                        except KeyboardInterrupt:
                            with open("settings.pkl", "wb") as file:
                                dump({"PR": PEOPLE_REPAIR}, file)
                            exit(-1)
                        # small_bar.write("翻译完成：{}".format(to))
                break
            else:
                if input("R or W") == "W":
                    PEOPLE_REPAIR[input("Key:")] = input("type")
                else:
                    print(PEOPLE_REPAIR)

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
        for FILE_NAME in big_bar:
            tree = ET.parse(source=FILE_NAME)
            root = tree.getroot()
            with tqdm(root.iter('string'), desc=FROM_FILE, total=len(list(root.iter()))) as small_bar:
                for elem in small_bar:
                    # small_bar.write("开始翻译：{}".format(elem.text))
                    to = smart_translate(elem.text)
                    elem.text = to
                    # small_bar.write("翻译完成：{}".format(to))
else:
    tree = ET.parse(source=FROM_FILE)
    root = tree.getroot()
    with tqdm(root.iter('string'), desc=FROM_FILE, total=len(list(root.iter('string')))) as small_bar:
        for elem in small_bar:
            # small_bar.write("开始翻译：{}".format(elem.text))
            to = smart_translate(elem.text)
            elem.text = to
            # small_bar.write("翻译完成：{}".format(to))
tree.write(SAVE_FILE)
