from os import listdir
from os.path import isfile, splitext
from pickle import dump, load
from random import randint
from hashlib import md5
from logging import basicConfig, warning, error, debug, DEBUG
from datetime import datetime
from typing import Optional, Tuple

from easygui import fileopenbox, filesavebox, diropenbox
from requests import post
import xml.etree.ElementTree as ET
from tqdm import tqdm

# 导入Inside模块中的APP_KEY和APP_ID
from Inside import inside_app_id, inside_app_key

"""
文件格式示例：
inside_app_id = '你的app_key'
inside_app_key = '你的app_key'
"""

# 用户字典和错误尝试次数常量
Inside_Usr = {"test": "0test0"}
ERR_TRIES = 3

# 用户选择启动模式
start_mode = input("选择启动模式\n0. 命令行模式\n1. 窗口模式\n2. 安全模式（独立配置）\n输入选项：")
# 根据启动模式配置日志和文件路径
if start_mode == "1":
    print("太可惜了，还梅能支持")
elif start_mode == "2":
    # 安全模式配置
    basicConfig(level=DEBUG, format='%(asctime)s [%(levelname)s] %(module)s %(message)s',
                datefmt='%Y-%m-%d %A %H:%M:%S', filename="SAFE{}MODE.log".format(datetime.now().strftime('%Y%m%d')),
                filemode='a')
    Settings_dir = "Settings_safe_mode.pkl"
    Brain_dir = "Brains_safe_mode.pkl"
    open(Brain_dir, "wb").close()
    open(Settings_dir, "wb").close()
else:
    # 命令行模式配置
    basicConfig(level=DEBUG, format='%(asctime)s [%(levelname)s] %(module)s %(message)s',
                datefmt='%Y-%m-%d %A %H:%M:%S', filename="{}.log".format(datetime.now().strftime('%Y%m%d')),
                filemode='a')
    Brain_dir = "Brains.pkl"
    Settings_dir = "Settings.pkl"
    # 尝试加载设置和知识库
    if Brain_dir in listdir():
        with open(Brain_dir, "rb") as file:
            Brain = load(file)
    else:
        Brain = dict()
    if Settings_dir in listdir():
        with open(Settings_dir, "rb") as file:
            Settings = load(file)
    else:
        Settings = {"Usr_name": "未登录用户", "Protect_key": None}


# 生成MD5摘要的函数
def make_md5(s, encoding='utf-8'):
    """
    生成MD5摘要。

    :param s: 需要生成摘要的字符串
    :param encoding: 字符串编码方式，默认为'utf-8'
    :return: 返回MD5摘要的十六进制字符串
    """
    return md5(s.encode(encoding)).hexdigest()


# 使用百度翻译API翻译文本的函数
def translate(query: str, appid: str, appkey: str, from_lang: str = "auto", to_lang: str = "zh",
              url: str = 'http://api.fanyi.baidu.com/api/trans/vip/translate',
              salt: int = randint(32768, 65536), tries: int = 0) -> str:
    """
    使用百度翻译API翻译文本。

    :param query: 需要翻译的文本
    :param appid: 百度翻译API的APP ID
    :param appkey: 百度翻译API的密钥
    :param from_lang: 源语言，默认为自动检测
    :param to_lang: 目标语言，默认为中文
    :param url: 百度翻译API的URL
    :param salt: 随机数，用于生成签名
    :param tries: 当前尝试次数
    :return: 翻译后的文本
    """
    global Brain, ERR_TRIES
    # 发起翻译请求
    r = post(url=url, headers={'Content-Type': 'application/x-www-form-urlencoded'},
             params={'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang,
                     'salt': salt,
                     'sign': make_md5(appid + query + str(salt) + appkey)}).json()
    debug(r)
    # 检查是否有错误
    if "error_code" in r.keys() or "error_msg" in r.keys():
        warning("错误代码：{}，错误信息：{}，出错文本：{}，尝试次数：{}".format(r["error_code"], r["error_msg"], query, tries))
        # 如果尝试次数超过限制，则停止请求
        if tries >= ERR_TRIES:
            warning("次数超出限制，自动停止请求")
            return query
        else:
            # 递归调用自身，增加尝试次数
            return translate(query=query, appid=appid, appkey=appkey, from_lang=from_lang, to_lang=to_lang, url=url,
                             salt=randint(32768, 65536), tries=tries + 1)
    else:
        result = r["trans_result"]
    # 如果翻译结果只有一个，则保存到知识库
    if len(result) == 1:
        Brain[result[0]["src"]] = result[0]["dst"]
    return result[0]["dst"]


# 智能翻译文本的函数
def smart_translate(text: str, appid: str, appkey: str) -> str:
    """
    智能翻译文本，尝试从知识库中查找，否则调用translate函数。

    :param text: 需要翻译的文本
    :param appid: 百度翻译API的APP ID
    :param appkey: 百度翻译API的密钥
    :return: 翻译后的文本
    """
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


# 加密函数
def encrypter(text: str, password: str) -> Tuple[str, str]:
    """
    加密文本。

    :param text: 需要加密的文本
    :param password: 加密密钥
    :return: 返回加密后的文本和测试密钥
    """
    output = str()
    test = str()
    passkey = int()
    for i in password:
        passkey += ord(i)
    for i in "Successfully":
        test += ord(i) * passkey
    for i in text:
        output += ord(i) * passkey
    return output, test


# 解密函数
def decrypter(text: str, password: str, test_key: Optional[str] = None) -> Tuple[Optional[str], bool]:
    """
    解密文本。

    :param text: 需要解密的文本
    :param password: 解密密钥
    :param test_key: 测试密钥
    :return: 返回解密后的文本和解密是否成功
    """
    output = str()
    passkey = int()
    test = str()
    for i in password:
        passkey += ord(i)
    for i in test_key:
        test += chr(i / passkey)
    if test != "Successfully":
        return None, False
    for i in text:
        output += chr(i / passkey)
    return output, True


# 打印欢迎信息
print("欢迎回来：{}".format(Settings["Usr_name"]))

# 获取用户输入的操作
operation = input(
    "选择操作\n0. 开始单文件处理\n1. 开始批量处理\n2. 开始测试（账号test，密码0test0）\n3. 设置\n输入选项：")

# 根据操作设置文件路径
FROM_FILE = SAVE_FILE = None
if operation == "0":
    # 单文件处理模式
    while FROM_FILE is None:
        print("请在打开的窗口中选择待处理的UI文件（如果没看到窗口，请检查是否被其它窗口遮挡）")
        FROM_FILE = fileopenbox(msg="选择待处理的UI文件", title="选择UI文件", filetypes=["*.ui", "*.xml"],
                                default="*.ui")
    while SAVE_FILE is None:
        print("请在打开的窗口中选择保存的UI文件（如果没看到窗口，请检查是否被其它窗口遮挡）")
        SAVE_FILE = filesavebox(msg="选择处理后UI保存位置", title="选择输出位置", filetypes=["*.ui", "*.xml"],
                                default="*.ui")
elif operation == "1":
    # 批量处理模式
    while FROM_FILE is None:
        print("请在打开的窗口中选择待处理的UI文件文件夹（如果没看到窗口，请检查是否被其它窗口遮挡）")
        FROM_FILE = diropenbox(msg="选择待处理的UI文件夹", title="选择UI文件夹", default="*.ui")
    while SAVE_FILE is None:
        print("请在打开的窗口中选择转换后UI保存的文件夹（如果没看到窗口，请检查是否被其它窗口遮挡）")
        SAVE_FILE = diropenbox(msg="选择处理后UI保存文件夹", title="选择输出位置", default="*.ui")
elif operation == "2":
    # 测试模式
    user_name = input("Enter Username:")
    pwd = input("Enter Password:")
    if user_name in Inside_Usr.keys() and Inside_Usr[user_name] == pwd:
        APP_ID = inside_app_id
        APP_KEY = inside_app_key
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
                            small_bar.write("开始翻译：{}".format(elem.text))
                            try:
                                to = smart_translate(text=elem.text, appid=APP_ID, appkey=APP_KEY)
                                elem.text = to
                            except KeyboardInterrupt:
                                with open("settings.pkl", "wb") as file:
                                    dump({"KNOWLEDGE": Brain}, file)
                                exit(-1)
                            small_bar.write("翻译完成：{}".format(to))
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
elif operation == "3":
    while True:
        choice_settings = input("输入选择的设置项：\n1. 重设本地储存内容加密密钥\n2. 重设用户APP ID\n 3. 重设用户密钥\n"
                                "4. 设置API服务器（不支持）\n5. 翻译知识库相关\n6. 换个名字\n7. 保存并关闭程序\n输入选项：")
        if choice_settings == "1":
            Settings["Protect_key"] = input("输入本地储存内容加密密钥（记住了，不然怕是你永远解锁不了。可以用中文哦）：")
        elif choice_settings == "2":
            if Settings["Protect_key"] is not None:
                Settings["APP_ID"] = encrypter(input("输入你从百度翻译开放平台获取的APP ID："), Settings["Protect_key"])[0]
            else:
                print("奶奶滴，你知道明文有多恐怖吗？你怕是明天免费额度就得跑完！快按1设置加密密钥")
        elif choice_settings == "3":
            if Settings["Protect_key"] is not None:
                Settings["APP_KEY"] = encrypter(input("输入你从百度翻译开放平台获取的密钥："), Settings["Protect_key"])[0]
            else:
                print("奶奶滴，你知道明文有多恐怖吗？你怕是明天免费额度就得跑完！快按1设置加密密钥")
        elif choice_settings == "4":
            print("不是说了用不了吗，你怎么不听呢？")
        elif choice_settings == "5":
            choice = input("输入 你干嘛：\n1. 让我看看\n2. 我来 设置")
            if choice == "1":
                for i in Brain.keys():
                    print("原文：{} 翻译：{}".format(i, Brain[i]))
            else:
                print("先输翻译后输原文哦")
                Brain[input("原文：")] = input("翻译：")
        elif choice_settings == "6":
            Settings["Usr_name"] = input("你想叫啥？\n")
        elif choice_settings == "7":
            with open("settings.pkl", "wb") as file:
                dump(Settings, file)
            exit(0)
        else:
            print("这个地方下次再来探索吧！")
else:
    input("不听话是把，不让你用了！（回车退出）")
    exit(66666)

# 打印ASCII艺术字
print(r"""
=====================================================================
=====================================================================
 ____    __  __  ____    ____    ____    ____              ____      
/\  _`\ /\ \/\ \/\  _`\ /\  _`\ /\  _`\ /\  _`\    /'\_/`\/\  _`\    
\ \ \L\_\ \ \ \ \ \ \L\ \ \ \L\_\ \ \L\ \ \ \/\_\ /\      \ \ \/\ \  
 \/_\__ \\ \ \_\ \ \ ,__/\ \  _\L\ \ ,  /\ \ \/_/_\ \ \__\ \ \ \_\ \ 
   \ \ \L\ \ \ \_\ \ \ \/  \ \ \L\ \ \ \\ \\ \ \L\ \\ \ \_/\ \ \ \_\ \
   \ `\____\ \_____\ \_\   \ \____/\ \_\ \_\ \____/ \ \_\\ \_\ \____/
    \/_____/\/_____/\/_/    \/___/  \/_/\/ /\/___/   \/_/ \/_/\/___/                                                                    
=====================================================================
=====================================================================
---------------------------------------------------------------------""")

# 根据用户选择的操作执行相应的处理
if operation == "1":
    # 批量处理模式：处理指定文件夹中的所有UI文件
    FILE_LIST = list()
    for FILE_NAME in listdir(FROM_FILE):
        if isfile(FILE_NAME) and splitext(FILE_NAME)[1] in ['.ui', '.xml']:
            FILE_LIST.append(FILE_NAME)
    with tqdm(FILE_LIST) as big_bar:
        for file in big_bar:
            tree = ET.parse(source=FROM_FILE + "\\" + file)
            root = tree.getroot()
            with tqdm(root.iter('string'), desc=FROM_FILE, total=len(list(root.iter('string')))) as small_bar:
                for elem in small_bar:
                    try:
                        small_bar.write("开始翻译：{}".format(elem.text))
                        try:
                            to = smart_translate(text=elem.text, appid=Settings["APP_ID"],
                                                 appkey=Settings["APP_KEY"])
                            elem.text = to
                        except KeyboardInterrupt:
                            with open("settings.pkl", "wb") as file:
                                dump({"KNOWLEDGE": Brain}, file)
                            exit(-1)
                        small_bar.write("翻译完成：{}".format(to))
                    except BaseException as err:
                        error(err)
            tree.write(SAVE_FILE + "\\" + file, encoding="utf-8")
    with open("settings.pkl", "wb") as file:
        dump(Settings, file)
    exit(0)
elif operation == "0":
    # 单文件处理模式：处理单个UI文件
    tree = ET.parse(source=FROM_FILE)
    root = tree.getroot()
    with tqdm(root.iter('string'), desc=FROM_FILE, total=len(list(root.iter('string')))) as small_bar:
        for elem in small_bar:
            try:
                small_bar.write("开始翻译：{}".format(elem.text))
                try:
                    to = smart_translate(text=elem.text, appid=Settings["APP_ID"],
                                         appkey=Settings["APP_KEY"])
                    elem.text = to
                except KeyboardInterrupt:
                    with open("settings.pkl", "wb") as file:
                        dump({"KNOWLEDGE": Brain}, file)
                    exit(-1)
                small_bar.write("翻译完成：{}".format(to))
            except BaseException as err:
                error(err)
    tree.write(SAVE_FILE, encoding="utf-8")
    with open("Brains.pkl", "wb") as file:
        dump(Brain, file)
