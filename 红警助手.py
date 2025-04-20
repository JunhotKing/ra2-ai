# -*- coding: utf-8 -*-

import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin

class RedAlertHelper:
    def __init__(self):
        self.faq_url = "https://help.yra2.com/faq"
        self.group_url = "https://www.yra2.com/group"
        self.sponsor_url = "https://www.yra2.com/sponsor/"
        self.cache_file = "redalert_cache.json"
        self.cache_expiry = timedelta(hours=24)
        self.faq_data = [
            {
                'question': '安装文件损坏或无法创建',
                'answer': '安装文件损坏将所有杀毒软件关闭，尤其是360、腾讯电脑管家、迈克菲(Mcfee)、联想电脑管家等杀毒软件。如果仍无法解决就重新下载，可能安装包已经被破坏。',
                'keywords': self._extract_keywords('安装损坏'),
                'category': '安装问题',
                'subcategory': '安装问题'
            },
            {
                'question': '我怎么启动游戏，找不到入口',
                'answer': '如果桌面上没有游戏快捷方式的话，游戏入口在安装文件夹里的 Reunion.exe 或 Reunion 2023.exe',
                'keywords': self._extract_keywords('启动游戏'),
                'category': '安装问题',
                'subcategory': '安装问题'
            },
            {
                'question': 'Win7 系统启动没有反应',
                'answer': '  如果你确实没搞错文件，那就下载并安装 Windows6.1-KB2670838 系统补丁：x64-windows6.1-kb2670838-x64.msux/x86-windows6.1-kb2670838-x86.msu',
                'keywords': self._extract_keywords('无反应'),
                'category': '安装问题',
                'subcategory': '安装问题'
            },
            {
                'question': '弹窗：You must install .NET Desktop Runtime......',
                'answer': '  安装.NET7(x86)运行库, 下载地址:https://alist.yra2.com/.NET7/x86/windowsdesktop-runtime-7.0.20-win-x86.exe    ,(如果Architecture部分提示的是x64或其他架构, 请根据实际情况安装对应架构的运行库[1.5版本已更换.NET6])',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '弹窗问题'
            },
            {
                'question': '弹窗：无法启动此程序，因为计算机中丢失 api-ms-win-crt-runtime-|1-1-0.dll...',
                'answer': '  需要安装 VC++2015-2022 运行库，或者你那里有 VC++2015-2019 也是可以的,VC++2015-2022下载地址: https://alist.yra2.com/VC++2015-2022',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '弹窗问题'
            },
            {
                'question': '弹窗：Main Client Library *** not found！',
                'answer': '不要把主程序直接拖到桌面上运行，你应该创建快捷方式。如果你觉得你做的没有问题，仍然出现此错误，请重新安装',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '弹窗问题'
            },
            {
                'question': '弹窗：若要运行此应用程序，您必须首先安装 .NET Framework v4.0.30319...',
                'answer': '.NET4.0 下载地址：https://alist.yra2.com/.NET4/dotNetFx40_Full_x86_x64.exe',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '弹窗问题'
            },
            {
                'question': '弹窗：Could not load executable',
                'answer': '关闭杀毒软件',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '弹窗问题'
            },
            {
                'question': '弹窗：停止工作',
                'answer': '尝试清理缓存或者管理员身份运行',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '弹窗问题'
            },
            {
                'question': '弹窗：FATAL……',
                'answer': ' 管理员模式运行',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '弹窗问题'
            },
            {
                'question': '多次提示使用新的名字, 例如: 您的名字已被占用，重试为Player_',
                'answer': '请在客户端设置—游戏—玩家名称更改（因为怕字库缺失，所以不支持中文名称）',
                'keywords': self._extract_keywords('重复名称'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '联机大厅连接到CnCNet但无法创建房间',
                'answer': '如果您是1.4.20版本，请查看Lobby servers行，如果后面显示的是0 fast，则证明连接失败(因为客户端没有找到在可接受延迟内的IRC服务器)，需要您多次重试连接或尝试更换网络(1.5版本已更换为自建服务器，并解决这个问题)',
                'keywords': self._extract_keywords('无法创建'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '进入联机大厅提示: AUTO Your IP address has been listed at DroneBL?',
                'answer': '如果是家庭带宽，重启路由器更换一个IP地址即可(不要再傻fufu的用客户端提供的链接去解封了，基本解不了，能解也算你运气好而已，DroneBL一般不搭理你的)，至于为什么会被封，在中国境内，如果你不是独立IP，那么一个IPv4就是几个人同时在用，你完全不能保证任何正在使用或者曾经使用过的人拿着这个IP干坏事',
                'keywords': self._extract_keywords('重复IP'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '为什么进入联机大厅会提示: Too many unknown connections form your IP?',
                'answer': '该问题对于1.5.0以上版本较为常见。众所周知，中国境内本身就是一个大型NAT网络，一群人共用同一个IPv4，就比较容易出现这种问题，可以等待15分钟左右再试，若仍无法解决请联系制作组获取帮助',
                'keywords': self._extract_keywords('共用IP'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '进入联机大厅报错提示: The connection speed is too fast?',
                'answer': '该问题通常发生在1.5.0以上版本，但触发概率极低。如果遇到此问题请稍等5-10秒左右再重新连接联机大厅',
                'keywords': self._extract_keywords('重新连接'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '局域网大厅报错创建Socket连接失败?',
                'answer': '请重启电脑后重新连接局域网大厅',
                'keywords': self._extract_keywords('报错'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '局域网游玩时弹窗报错？',
                'answer': '游戏过程中弹窗，清理缓存重试，等后续版本优化',
                'keywords': self._extract_keywords('弹窗报错'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '创建局域网Socket失败！',
                'answer': '重启电脑',
                'keywords': self._extract_keywords('失败'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '进入联机大厅出现闪退',
                'answer': '重启电脑',
                'keywords': self._extract_keywords('闪退'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '进入联机大厅显示ERROR:Closing Linlk……',
                'answer': '如果你的网络DNS不是自动的，请反馈给群管理（运营组-Shiroko）',
                'keywords': self._extract_keywords('网络'),
                'category': '启动问题',
                'subcategory': '联机问题'
            },
            {
                'question': '开始游戏立马弹回客户端',
                'answer': '关闭你的杀毒软件，如果还不行,重启电脑',
                'keywords': self._extract_keywords('闪退'),
                'category': '开始异常',
                'subcategory': '出现问题'
            },
            {
                'question': '开始后游戏直接黑屏没有反应',
                'answer': '如果你确定不是2人图放了三个人的话, 可以尝试不要使用随机位置, 或者换图, 还不行就去设置-游戏里清理游戏缓存重试',
                'keywords': self._extract_keywords('黑屏'),
                'category': '开始异常',
                'subcategory': '出现问题'
            },
            {
                'question': '打完了一直黑屏出不来',
                'answer': '如果您的系统是Windows11，24H2, 这是因为微软改了系统内核所致(且该版本目前由微软印度维护)。目前已在1.5版本中修复(打开客户端设置里的多核心运行), 群文件有安装包(还在持续测试中，不公开下载), 使用前记得关闭杀毒软件(360、腾讯电脑管家等)安装。',
                'keywords': self._extract_keywords('黑屏'),
                'category': '开始异常',
                'subcategory': '出现问题'
            },
            {
                'question': '弹窗：.NET Host 已停止工作',
                'answer': '在客户端设置中将渲染补丁更改成默认',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '开始异常'
            },
            {
                'question': '弹窗：出现错误：System.UnauthorizedAccessException',
                'answer': '请检查是否开启了杀毒软件, 并尝试清理缓存(这个问题可能是杀毒拦截所致)，临时解决办法：顺着路径找到这个文件，右键属性，换到常规页面，文件的只读属性去掉',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '开始异常'
            },
            {
                'question': '弹窗：Could not run executable',
                'answer': '退出客户端并重新以管理员模式运行',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '开始异常'
            },
            {
                'question': '弹窗：CnCMaps已停止工作',
                'answer': '这个报错是因为地图高清预览图渲染出错导致，忽略即可，不影响游戏(如果想要解决可以在客户端设置里关闭)',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '开始异常'
            },
            {
                'question': '弹窗：Unable to initialize',
                'answer': '换个游戏目录重新安装, 大概率是因为安装路径太长，或者某个文件夹名称太长',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '开始异常'
            },
            {
                'question': '弹窗：系统策略禁止这个安装，请与系统管理员联系',
                'answer': '  打开gpedit.msc—计算机配置—管理模板—Windows组件—windows installer,关闭Windows Installer"设置为"已禁用"，然后点应用，确定',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '开始异常'
            },
            {
                'question': '进入游戏后按ESC会卡住?',
                'answer': '如果是1.4.20版本, 请尝试关闭杀毒或使用官网的ddraw修复脚本修复, 如果是Win11,24H2必须使用1.5测试版本',
                'keywords': self._extract_keywords('卡住'),
                'category': '游戏问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '感觉视野不合适，太大/太小',
                'answer': '在客户端设置里适当降低游戏分辨率，分辨率越高视野越大, 物件越小,官方建议游戏分辨率最大不超过2560*1440, 客户端分辨率最大不超过4096*2160',
                'keywords': self._extract_keywords('视野'),
                'category': '游戏问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '屏幕滑动太快\太慢',
                'answer': '客户端设置点击：游戏—屏幕滑动速度，根于个人喜好设置滑动速度（建议速度3）',
                'keywords': self._extract_keywords('滑动'),
                'category': '游戏问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '怎么不能按Shift连点了？',
                'answer': '  任务使用名称末尾带+的模组即可。如果默认是第三方模组请不要随意更改(可能会导致任务包运行异常)',
                'keywords': self._extract_keywords('连点'),
                'category': '游戏问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '为什么无法攻击敌人？敌人也不攻击我  /我想1打7应该怎么设置？',
                'answer': '  小队为相同字母的为一队，‘-’代表自成一队。',
                'keywords': self._extract_keywords('无法'),
                'category': '游戏问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '弹窗：需要使用新应用以打开此ms-gamingoverlay链接?',
                'answer': '此问题通常只会在Win10 1903及更高的系统中出现, 是因为系统缺少Xbox Game Bar组件导致, 点击此连接可跳转至Microsoft Store安装：https://apps.microsoft.com/detail/9nzkpstsnw4p?hl=zh-cn&gl=CN   ，若您的Win10/11系统阉割掉了微软商店, 可以点此下载appx独立安装包进行安装：https://archive.ru2023.top/win/xbox/Microsoft.XboxGamingOverlay_7.225.2131.0_neutral_~_8wekyb3d8bbwe.AppxBundle   ，如果你实在不想安装的话直接禁用掉也可以, 这里使用微软官方社区提供的方法：https://answers.microsoft.com/en-us/windows/forum/all/get-an-app-for-ms-gamingoverlay/c29dd6a6-544d-49a2-ae03-7ee1b47bfab1   (英文看不懂就自己找工具翻译一下)，对于Win11的老坛酸菜版本(Win11 24H2 LTSC)来说, 如果独立包也无法安装, 那就只能通过最后的注册表方法禁用, 阿三这版本精简的太过头了',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '弹窗：本产品需要16位原色盘',
                'answer': '游戏客户端设置cnc-ddraw即可',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '弹窗：Exception Processing……',
                'answer': '打开客户端设置点游戏，关闭后台渲染即可',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '弹窗：意外的致命错误……',
                'answer': '重启电脑试试，并尝试管理员身份运行',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '弹窗：Fatal Error',
                'answer': '关闭一些功能即可，功能开的越多，弹窗几率越大',
                'keywords': self._extract_keywords('弹窗'),
                'category': '弹窗问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '声明',
                'answer': '！！！开修改大师造成的游戏弹窗开发组一律不负责！！！',
                'keywords': self._extract_keywords('报错'),
                'category': '其他内容',
                'subcategory': '其他'
            },
            {
                'question': '开始游戏出现黑屏、无反应…',
                'answer': '客户端设置启用多核运行',
                'keywords': self._extract_keywords('黑屏'),
                'category': 'w11问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '使用拼音输入法闪退、死机问题',
                'answer': '这是微软的一个屎山问题，因此我们找到了解决方法（此问题影响大部分Win11版本)，可以使用小狼毫输入法（网址：https://rime.im/   ）具体："见输入法"',
                'keywords': self._extract_keywords('黑屏'),
                'category': 'w11问题',
                'subcategory': '游戏问题'
            },
            {
                'question': '输入法',
                'answer': '小狼毫输入法网址：https://rime.im/   ，安装教程引用小狼毫官网：https://www.cnblogs.com/HookDing/p/17949199   ，雾凇字库文件网址：https://github.com/iDvel/rime-ice/releases/tag/nightly',
                'keywords': self._extract_keywords(''),
                'category': '其他内容',
                'subcategory': '其他'
            },
            {
                'question': '赞助支持',
                'answer': '赞助支持：https://www.yra2.com/sponsor/',
                'keywords': self._extract_keywords('赞助支持'),
                'category': '其他内容',
                'subcategory': '其他'
            },
            {
                'question': '更多内容',
                'answer': '更多内容见文档：https://help.yra2.com/faq',
                'keywords': self._extract_keywords('文档'),
                'category': '其他内容',
                'subcategory': '其他'
            },
            {
                'question': '安全中心关闭方法',
                'answer': '请关闭所有安全中心和杀毒软件，尤其是360、腾讯电脑管家、迈克菲(Mcfee)、联想电脑管家等。',
                'keywords': self._extract_keywords('关杀毒'),
                'category': '其他内容',
                'subcategory': '其他'
            },
        ]
        self.group_numbers = [
            {"name": "QQ交流1群", "number": "363035291", "status": "已满"},
            {"name": "QQ交流2群", "number": "561178527", "status": "已满"},
            {"name": "QQ交流3群", "number": "185228408", "status": "已满"},
            {"name": "QQ交流4群", "number": "342784372", "status": "已满"},
            {"name": "QQ交流5群", "number": "342759792", "status": "可用"},
            {"name": "QQ交流6群", "number": "157382537", "status": "可用"},
            {"name": "QQ交流7群", "number": "194533292", "status": "可用"},
            {"name": "QQ交流8群", "number": "342091822", "status": "可用"},
            {"name": "QQ交流9群", "number": "955215881", "status": "可用"},
            {"name": "QQ交流10群", "number": "759895622", "status": "可用"},
        ]

    def _extract_keywords(self, text):
        """提取关键词"""
        words = re.findall(r'[\w\u4e00-\u9fa5]{2,}', text.lower())
        return list(set(words))

    def debug_data_status(self):
        """调试数据状态"""
        print(f"\n当前数据状态：")
        print(f"- 加载解决方法数量: {len(self.faq_data)}条")
        print(f"- 群号数量: {len(self.group_numbers)}个")
        if self.faq_data:
            print(f"- 示例解决方法: {self.faq_data[0]['question'][:50]}...")

    def show_results(self, results, question=None):
        """显示搜索结果"""
        if not results:
            print("\n未找到相关解答，请选择以下官方QQ交流群：")
            for group in self.group_numbers:
                print(f"{group['name']}：{group['number']} ({group['status']})")
            print(f"\n其他群聊访问：{self.group_url}")
            print(f"问题解决访问：{self.faq_url}")
            print(f"赞助支持：{self.sponsor_url}")
            return False
        else:
            print(f"\n为您找到以下相关解答：")
            for i, res in enumerate(results[:3], 1):
                print(f"{i}. [相关度:{res['score']:.2f}] {res['data']['question']}")
                print(f"   {res['data']['answer'][:100]}...\n")
            return True

    def get_specific_answer(self, question):
        """获取特定问题的解答"""
        for item in self.faq_data:
            if question.lower() in item['question'].lower():
                return item['answer']
        return None

    def interactive_faq(self):
        """交互式查看所有解决方法"""
        print("\n===== 目录 =====")
        categories = list(set(item['category'] for item in self.faq_data))
        
        for category in categories:
            print(f"\n===== {category} =====")
            subcategories = list(set(item['subcategory'] for item in self.faq_data if item['category'] == category))
            
            for subcategory in subcategories:
                print(f"\n---- {subcategory} ----")
                subcategory_items = [item for item in self.faq_data if item['category'] == category and item['subcategory'] == subcategory]
                
                for i, faq in enumerate(subcategory_items, 1):
                    print(f"{i}. {faq['question']}")
                
                while True:
                    user_input = input("\n选择问题编号（输入t退出，输入x查看下一小类，输入s返回上一大类）：").strip()
                    
                    if user_input.lower() == 't':
                        return
                    elif user_input.lower() == 'x':
                        break
                    elif user_input.lower() == 's':
                        break
                    
                    try:
                        index = int(user_input) - 1
                        if 0 <= index < len(subcategory_items):
                            print(f"\n问题：{subcategory_items[index]['question']}")
                            print(f"解答：{subcategory_items[index]['answer']}")
                        else:
                            print("无效的编号，请重新输入。")
                    except ValueError:
                        print("请输入有效的数字、t退出、x查看下一小类或s返回上一大类。")

    def levenshtein_distance(self, a, b):
        """计算两个字符串的Levenshtein距离"""
        m, n = len(a), len(b)
        if m == 0:
            return n
        if n == 0:
            return m

        # 创建一个矩阵来存储距离
        matrix = [[0] * (n + 1) for _ in range(m + 1)]
        
        # 初始化矩阵
        for i in range(m + 1):
            matrix[i][0] = i
        for j in range(n + 1):
            matrix[0][j] = j

        # 填充矩阵
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,      # 删除
                    matrix[i][j - 1] + 1,      # 插入
                    matrix[i - 1][j - 1] + cost  # 替换
                )
        
        return matrix[m][n]

    def calculate_similarity(self, a, b):
        """计算两个字符串的相似度（0到1之间）"""
        distance = self.levenshtein_distance(a, b)
        max_len = max(len(a), len(b))
        return 1 - (distance / max_len)

    def search(self, question):
        """增强版搜索（支持模糊匹配）"""
        query_keywords = set(self._extract_keywords(question))
        results = []

        for item in self.faq_data:
            # 计算匹配度
            content_keywords = set(item['keywords'])
            match_score = len(query_keywords & content_keywords)
            
            # 标题匹配权重更高
            title_match = sum(
                1 for kw in query_keywords 
                if kw in item['question'].lower()
            )
            
            # 模糊匹配
            similarity_score = 0
            for kw in query_keywords:
                similarity = self.calculate_similarity(kw, item['question'].lower())
                if similarity > 0.6:  # 设置相似度阈值
                    similarity_score += similarity
            
            # 综合匹配度
            total_score = match_score * 2 + title_match + similarity_score * 0.5  # 模糊匹配权重较低
            
            if match_score > 0 or title_match > 0 or similarity_score > 0:
                results.append({
                    'score': total_score,
                    'data': item
                })
        
        return sorted(results, key=lambda x: -x['score'])

def main():
    helper = RedAlertHelper()
    helper.debug_data_status()
    
    # 交互模式
    while True:
        print("\n请输入您的问题：")
        print("输入t退出，输入查看，即可查看所有解决方法")
        print("所有字母不分大小写")
        user_input = input("> ").strip()
        
        if user_input.lower() == 't':
            break
            
        if user_input.lower() == '查看':
            helper.interactive_faq()
            continue
            
        results = helper.search(user_input)
        helper.show_results(results, user_input)

if __name__ == "__main__":
    main()
    
     #格式:
            #{
                #'question': ' ',
                #'answer': ' ',
                #'keywords': self._extract_keywords(' '),
                #'category': ' ',
                #'subcategory': ' '
            #},
                #问题：question
                #回答：answer
                #关键字：keywords
                #类别：category
                #子类别：subcategory