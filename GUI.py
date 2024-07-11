from easygui import fileopenbox, filesavebox, diropenbox
DIR_MODE = input("选择启动模式\n0. 单文件处理模式\n1. 批量处理模式\n")
FROM_FILE = SAVE_FILE = None
if DIR_MODE:
    while FROM_FILE is None:
        FROM_FILE = diropenbox(msg="选择待处理的UI文件夹", title="选择UI文件夹", default="*.ui")
    while SAVE_FILE is None:
        SAVE_FILE = diropenbox(msg="选择处理后UI保存文件夹", title="选择输出位置", default="*.ui")
elif DIR_MODE:
    while FROM_FILE is None:
        FROM_FILE = fileopenbox(msg="选择待处理的UI文件", title="选择UI文件", filetypes=["*.ui", "*.xml"],
                                default="*.ui")
    while SAVE_FILE is None:
        SAVE_FILE = filesavebox(msg="选择处理后UI保存位置", title="选择输出位置", filetypes=["*.ui", "*.xml"], default="*.ui")
else:
    exit(0)