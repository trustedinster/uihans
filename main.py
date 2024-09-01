import os
import pickle
import random
import hashlib
import logging
from datetime import datetime
from typing import Optional, Tuple, List
from easygui import fileopenbox, diropenbox, filesavebox
import xml.etree.ElementTree as ET
from tqdm import tqdm
from requests import post
from os.path import splitext

from Inside import inside_app_id, inside_app_key


# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(module)s %(message)s',
                    datefmt='%Y-%m-%d %A %H:%M:%S', filename="{}.log".format(datetime.now().strftime('%Y%m%d')),
                    filemode='a')

print(r"""=====================================================================
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


class TranslationHelper:
    # 用户字典和错误尝试次数常量
    Inside_Usr = {"test": "0test0"}
    ERR_TRIES = 3

    # 配置文件字典项
    DICT_SHOULD_HAVE = ['Usr_name', 'Protect_key', 'APP_ID', 'APP_ID_TEST_WORD',
                        'APP_KEY', 'APP_KEY_TEST_WORD', 'DEFAULT_UPDATE_SERVER']
    def __init__(self, settings_file="settings.pkl", brain_file="Brains.pkl"):
        self.settings_file = settings_file
        self.brain_file = brain_file
        self.settings = self.load_settings()
        self.brain = self.load_brain()
        self.inside_app_id = inside_app_id
        self.inside_app_key = inside_app_key

    def make_sm3(self,s):
        """
            sm3密码杂凑计算函数，参数输入为长度小于2^64比特的消息串，返回由16进制字符串表示的256位杂凑值
            """

        # 初始值，用于确定压缩函数寄存器的状态
        V = 0x7380166f4914b2b9172442d7da8a0600a96f30bc163138aae38dee4db0fb0e4e

        # 算法中“字”定义为32位的比特串
        MAX_32 = 0xffffffff

        # 32位循环左移
        def lshift(x: int, i: int) -> int:
            return ((x << (i % 32)) & MAX_32) + (x >> (32 - i % 32))

        # 常量T，用于计算
        def T(j: int) -> int:
            if 0 <= j <= 15:
                return 0x79cc4519
            return 0x7a879d8a

        # 布尔函数FFj
        def FF(j: int, x: int, y: int, z: int) -> int:
            if 0 <= j <= 15:
                return x ^ y ^ z
            return (x & y) | (x & z) | (y & z)

        # 布尔函数GGj
        def GG(j: int, x: int, y: int, z: int) -> int:
            if 0 <= j <= 15:
                return x ^ y ^ z
            return (x & y) | (~x & z)

        # 置换函数P0
        def P0(x: int) -> int:
            return x ^ lshift(x, 9) ^ lshift(x, 17)

        # 置换函数P1
        def P1(x: int) -> int:
            return x ^ lshift(x, 15) ^ lshift(x, 23)

        # 消息填充函数，对长度为l(l < 2^64)比特的消息s，填充至长度为512比特的倍数
        def fill(s: str) -> str:
            v = 0
            for i in s:
                v <<= 8
                v += ord(i)
            msg = bin(v)[2:].zfill(len(s) * 8)
            k = (960 - len(msg) - 1) % 512
            return hex(int(msg + '1' + '0' * k + bin(len(msg))[2:].zfill(64), 2))[2:]

        m = fill(s)

        # 迭代过程
        for i in range(len(m) // 128):

            # 消息扩展
            Bi = m[i * 128: (i + 1) * 128]
            W = []
            for j in range(16):
                W.append(int(Bi[j * 8: (j + 1) * 8], 16))

            for j in range(16, 68):
                W.append(P1(W[j - 16] ^ W[j - 9] ^ lshift(W[j - 3], 15)) ^ lshift(W[j - 13], 7) ^ W[j - 6])
            W_ = []
            for j in range(64):
                W_.append(W[j] ^ W[j + 4])

            A, B, C, D, E, F, G, H = [V >> ((7 - i) * 32) & MAX_32 for i in range(8)]

            # 迭代计算
            for j in range(64):
                ss1 = lshift((lshift(A, 12) + E + lshift(T(j), j)) & MAX_32, 7)
                ss2 = ss1 ^ lshift(A, 12)
                tt1 = (FF(j, A, B, C) + D + ss2 + W_[j]) & MAX_32
                tt2 = (GG(j, E, F, G) + H + ss1 + W[j]) & MAX_32
                D = C
                C = lshift(B, 9)
                B = A
                A = tt1
                H = G
                G = lshift(F, 19)
                F = E
                E = P0(tt2)
            V ^= ((A << 224) + (B << 192) + (C << 160) + (D << 128) + (E << 96) + (F << 64) + (G << 32) + H)
        return hex(V)[2:].zfill(64)  # 返回256比特结果（16进制表示）

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "rb") as file:
                return pickle.load(file)
        else:
            return {"Usr_name": "未登录用户", "Protect_key": None, "DEFAULT_UPDATE_SERVER": "Gitee"}

    def load_brain(self):
        if os.path.exists(self.brain_file):
            with open(self.brain_file, "rb") as file:
                return pickle.load(file)
        else:
            return {}

    def save_settings(self):
        with open(self.settings_file, "wb") as file:
            pickle.dump(self.settings, file)

    def save_brain(self):
        with open(self.brain_file, "wb") as file:
            pickle.dump(self.brain, file)

    def is_right(self, text: dict) -> bool:
        for t in self.DICT_SHOULD_HAVE:
            if t not in text.keys():
                return False
        for t in text.keys():
            if text[t] is None:
                return False
        return True

    def make_md5(self, s: str, encoding: str = 'utf-8') -> str:
        return hashlib.md5(s.encode(encoding)).hexdigest()

    def encrypter(self, text: str, password: str) -> Tuple[List[int], List[int]]:
        """
        加密文本。

        :param text: 需要加密的文本
        :param password: 加密密钥
        :return: 返回加密后的文本和测试密钥
        """
        output = list()
        test = list()
        passkey = int()
        for char in password:
            passkey += ord(char)
        for char in "Successfully":
            test.append(ord(char) * passkey)
        for char in text:
            output.append(ord(char) * passkey)
        return output, test

    def decrypter(self, text: List[int], password: str, test_key: list) -> Tuple[Optional[str], bool]:
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
        for t in password:
            passkey += ord(t)
        for t in test_key:
            test += chr(int(t / passkey))
        if test != "Successfully":
            return None, False
        for t in text:
            output += chr(int(t / passkey))
        return output, True

    def translate(self, query: str, appid: str, appkey: str, from_lang: str = "auto", to_lang: str = "zh",
                  url: str = 'http://api.fanyi.baidu.com/api/trans/vip/translate',
                  salt: int = random.randint(32768, 65536), tries: int = 0) -> str:
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
                         'sign': self.make_md5(appid + query + str(salt) + appkey)}).json()
        logging.debug(r)
        # 检查是否有错误
        if "error_code" in r.keys() or "error_msg" in r.keys():
            logging.warning(
                "错误代码：{}，错误信息：{}，出错文本：{}，尝试次数：{}".format(r["error_code"], r["error_msg"], query,
                                                                         tries))
            # 如果尝试次数超过限制，则停止请求
            if tries >= ERR_TRIES:
                logging.warning("次数超出限制，自动停止请求")
                return query
            else:
                # 递归调用自身，增加尝试次数
                return self.translate(query=query, appid=appid, appkey=appkey, from_lang=from_lang, to_lang=to_lang,
                                      url=url,
                                      salt=random.randint(32768, 65536), tries=tries + 1)
        else:
            result = r["trans_result"]
            # 如果翻译结果只有一个，则保存到知识库
            if len(result) == 1:
                Brain[result[0]["src"]] = result[0]["dst"]
            return result[0]["dst"]

    def smart_translate(self, text: str, appid: str, appkey: str) -> str:
        """
        智能翻译文本，尝试从知识库中查找，否则调用translate函数。

        :param text: 需要翻译的文本
        :param appid: 百度翻译API的APP ID
        :param appkey: 百度翻译API的密钥
        :return: 翻译后的文本
        """
        if '\n' in text:
            logging.warning("无法适应带回车的字符：{}".format(text))
            return text
        global Brain
        out = str()
        try:
            split_texts = text.split(' ')
        except AttributeError:
            return self.translate(text, appid, appkey)
        else:
            for split_text in split_texts:
                if split_text in Brain.keys():
                    out += Brain[split_text]
                else:
                    out += self.translate(split_text, appid, appkey)
        return out

    def process_files(self, operation: str):
        """
        处理文件。

        :param operation: 操作模式，例如 "0" 表示单文件处理，"1" 表示批量处理
        """
        if operation == "0":
            # 单文件处理模式
            while True:
                FROM_FILE = fileopenbox(msg="选择待处理的UI文件", title="选择UI文件", filetypes=["*.ui", "*.xml"])
                if FROM_FILE is None:
                    break
                SAVE_FILE = filesavebox(msg="选择处理后UI保存位置", title="选择输出位置",
                                        filetypes=["*.ui", "*.xml"])
                if SAVE_FILE is None:
                    break
                tree = ET.parse(source=FROM_FILE)
                root = tree.getroot()
                with tqdm(total=len(list(root.iter('string'))), desc=FROM_FILE) as progress_bar:
                    for elem in root.iter('string'):
                        try:
                            to = self.smart_translate(text=elem.text, appid=self.settings["APP_ID"],
                                                      appkey=self.settings["APP_KEY"])
                            elem.text = to
                            progress_bar.update(1)
                        except KeyboardInterrupt:
                            self.save_settings()
                            self.save_brain()
                            exit(-1)
                        progress_bar.set_description("正在翻译：{}".format(elem.text))
                tree.write(SAVE_FILE, encoding="utf-8")
        elif operation == "1":
            # 批量处理模式
            FROM_FILE = diropenbox(msg="选择待处理的UI文件文件夹", title="选择UI文件夹")
            SAVE_FILE = diropenbox(msg="选择转换后UI保存文件夹", title="选择输出位置")
            FILE_LIST = []
            for FILE_NAME in os.listdir(FROM_FILE):
                if os.path.isfile(os.path.join(FROM_FILE, FILE_NAME)) and splitext(FILE_NAME)[1] in ['.ui', '.xml']:
                    FILE_LIST.append(FILE_NAME)
            for file in tqdm(FILE_LIST, desc="批量处理文件", total=len(FILE_LIST)):
                tree = ET.parse(os.path.join(FROM_FILE, file))
                root = tree.getroot()
                for elem in root.iter('string'):
                    try:
                        to = self.smart_translate(text=elem.text, appid=self.settings["APP_ID"],
                                                  appkey=self.settings["APP_KEY"])
                        elem.text = to
                    except KeyboardInterrupt:
                        self.save_settings()
                        self.save_brain()
                        exit(-1)
                tree.write(os.path.join(SAVE_FILE, file), encoding="utf-8")

    def set_mode(self):
        """
        设置模式。
        """
        while True:
            choice_settings = input(
                "输入选择的设置项：\n"
                f"1. 重设本地储存内容加密密钥（配置状态：{"已配置" if self.settings["Protect_key"] is not None else "未配置"}）\n"
                f"2. 重设用户APP ID（配置状态：{"已配置" if self.settings["APP_ID"] is not None else "未配置"}）\n"
                f"3. 重设用户密钥（配置状态：{"已配置" if self.settings["APP_KEY"] is not None else "未配置"}）\n"
                "4. 设置API服务器（不支持）\n"
                "5. 翻译知识库相关\n"
                "6. 换个名字\n"
                "7. 保存并退出设置模式\n"
                "输入选项：")
            if choice_settings == "1":
                self.settings["Protect_key"] = self.make_sm3(
                    input("输入本地储存内容加密密钥"
                          "（由于加密方式不可逆【国密SM3】，所以忘了就再也找不回来了。建议使用中文，保密性更好）："))
            elif choice_settings == "2":
                if self.settings["Protect_key"] is not None:
                    self.settings["APP_ID"], self.settings["APP_ID_TEST_WORD"] = self.encrypter(
                        input("输入你从百度翻译开放平台获取的APP ID："), self.settings["Protect_key"])
                else:
                    print("奶奶滴，你知道明文有多恐怖吗？你怕是明天免费额度就得跑完！快按1设置加密密钥")
            elif choice_settings == "3":
                if self.settings["Protect_key"] is not None:
                    self.settings["APP_KEY"], self.settings["APP_KEY_TEST_WORD"] = self.encrypter(
                        input("输入你从百度翻译开放平台获取的密钥："), self.settings["Protect_key"])
                else:
                    print("奶奶滴，你知道明文有多恐怖吗？你怕是明天免费额度就得跑完！快按1设置加密密钥")
            elif choice_settings == "4":
                print("不是说了用不了吗，你怎么不听呢？")
            elif choice_settings == "5":
                choice = input("输入 你干嘛：\n1. 让我看看\n2. 我来 设置\n输入选项：")
                if choice == "1":
                    for i in self.brain.keys():
                        print("原文：{} 翻译：{}".format(i, self.brain[i]))
                else:
                    print("先输翻译后输原文哦")
                    self.brain[input("原文：")] = input("翻译：")
            elif choice_settings == "6":
                self.settings["Usr_name"] = input("你想叫啥？\n")
            elif choice_settings == "7":
                with open(self.settings_file, "wb") as file:
                    pickle.dump(self.settings, file)
                return
            else:
                print("这个地方下次再来探索吧！")

if __name__ == "__main__":
    while True:
        helper = TranslationHelper()
        # 初始化配置
        if not helper.is_right(helper.settings):
            logging.warning("配置文件不合法，请检查")
            helper.settings = \
                {"Usr_name": "未登录用户", "Protect_key": None,
                 "DEFAULT_UPDATE_SERVER": "Gitee", "APP_ID": None, "APP_KEY": None}
            input("由于你未设定个人接口信息，无法正常完成功能，回车键开始配置\n")
            operation = "2"
        else:
            key = helper.make_md5(input("输入设置的本地存储内容加密密钥："))
            APP_ID, state1 = helper.decrypter(helper.settings["APP_ID"], key, helper.settings["APP_ID_TEST_WORD"])
            APP_KEY, state2 = helper.decrypter(helper.settings["APP_KEY"], key, helper.settings["APP_KEY_TEST_WORD"])
            if state1 or state2:
                print("无法解码，账号或密码出现问题。如果想重新输入，请重启程序")
                input("回车进行密码忘记处理")
                print("由于密码")
                operation = "2"
            else:
                # 获取用户输入的操作
                operation = input(
                    "选择操作\n0. 开始单文件处理\n1. 开始批量处理\n2. 设置\n输入选项：")
        # 执行操作
        if operation in ["0", "1"]:
            helper.process_files(operation)
        elif operation == "2":
            # 设置模式
            helper.set_mode()
        else:
            input("不听话是把，不让你用了！（回车退出）")