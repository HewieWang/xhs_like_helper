import os
import json
import time,sys
from playwright.sync_api import sync_playwright, TimeoutError

# 设置保存cookie的目录
COOKIE_DIR = "./cookies"
if not os.path.exists(COOKIE_DIR):
    os.makedirs(COOKIE_DIR)

# 账户计数器文件
COUNTER_FILE = os.path.join(COOKIE_DIR, "counter.txt")

# 代理文件路径
PROXY_FILE = "./proxy.json"

# 初始化或读取账户计数器
def get_next_account_number():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as f:
            counter = int(f.read().strip())
    else:
        counter = 0
    counter += 1
    with open(COUNTER_FILE, 'w') as f:
        f.write(str(counter))
    return counter

# 读取保存的cookie
def load_cookies(browser_context, cookie_file):
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
            browser_context.add_cookies(cookies)
        return True
    return False

# 保存cookie
def save_cookies(browser_context, cookie_file):
    cookies = browser_context.cookies()
    with open(cookie_file, 'w') as f:
        json.dump(cookies, f)


# 读取代理列表
def load_proxies():
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, 'r') as f:
            return json.load(f)
    return []

# 测试代理可用性
def test_proxy(proxy):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(proxy=proxy)
            page = context.new_page()
            page.goto("https://www.xiaohongshu.com", timeout=10000)  # 测试访问一个简单的页面
            browser.close()
        return True
    except Exception as e:
        print(f"Proxy {proxy['server']} failed: {e}")
        return False

# 获取可用代理
def get_working_proxy():
    proxies = load_proxies()
    for proxy in proxies:
        if test_proxy(proxy):
            return proxy
    raise Exception("No working proxies found")

# 检查是否登录成功
def check_login_status(page):
    while True:
        try:
            # 使用 locator 方法等待第一个匹配元素出现
            element = page.locator("li.user.side-bar-component span.channel").first
            # 等待元素可见
            element.wait_for(state="visible", timeout=5000)
            if element.inner_text() == "我":
                return True
        except TimeoutError:
            pass
        time.sleep(1)

def ensure_xiaohongshu_url(input_string):
    if "http" not in input_string:
        input_string = "https://www.xiaohongshu.com/explore/" + input_string
    return input_string

# 自定义函数：根据需要实现
def custom_function_for_account(page, account_name):
    # 实现你的自定义逻辑
    print(f"正在操作点赞 {account_name}")
    # notes=[
    #     "https://www.xiaohongshu.com/explore/664ab2bb00000000150137d6",
    #     "https://www.xiaohongshu.com/explore/664da40c000000000c019638",
    #     "https://www.xiaohongshu.com/explore/6636fa44000000001e034238"
    # ]
    # for n in notes:
    #     page.goto(ensure_xiaohongshu_url(n))
    #     page.click(".interactions.engage-bar .like-lottie")
    # pass

    file = open('notes.txt', 'r')
    for line in file:
        print("正在点赞:"+line)
        page.goto(ensure_xiaohongshu_url(line))
        page.click(".interactions.engage-bar .like-lottie")
    file.close()

    print(f"{account_name} 点赞完毕")
    page.close()

def main():
    # python xhs.py new
    # python xhs.py like
    new_account = "new" in sys.argv
    zan = "like" in sys.argv

    # 获取可用代理
    proxy = get_working_proxy()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(proxy=proxy)

        # 注入隐匿性脚本
        stealth_script_path = './stealth.min.js'
        context.add_init_script(path=stealth_script_path)

        if not new_account:
            # 遍历cookie文件，加载并尝试登录
            for cookie_file in os.listdir(COOKIE_DIR):
                if cookie_file == "counter.txt":
                    continue
                account_name, _ = os.path.splitext(cookie_file)
                cookie_path = os.path.join(COOKIE_DIR, cookie_file)

                if load_cookies(context, cookie_path):
                    page = context.new_page()
                    page.goto("https://www.xiaohongshu.com/explore", timeout=0)
                    if check_login_status(page):
                        print(f"Login successful for {account_name}")
                        if zan:
                            custom_function_for_account(page, account_name)
                            pass
                        
                    else:
                        print(f"Failed to login with saved cookies for {account_name}")
                    page.close()

        # 手动登录过程
        page = context.new_page()
        page.goto("https://www.xiaohongshu.com/explore", timeout=0)
        # page.click(".login-btn", timeout=0)
        print("Please log in manually...")

        # 等待用户手动完成登录
        if check_login_status(page):
            print("Login successful")
            account_number = get_next_account_number()
            account_name = f"account_{account_number}"
            cookie_path = os.path.join(COOKIE_DIR, f"{account_name}.json")
            save_cookies(context, cookie_path)
            if zan:
                custom_function_for_account(page, account_name)
                pass
            

        page.close()
        browser.close()

if __name__ == "__main__":
    main()