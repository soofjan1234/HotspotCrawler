import os
import sys
import tempfile

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发环境和打包环境"""
    try:
        # PyInstaller创建的临时文件夹
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def check_chrome_browser():
    """检查Chrome浏览器是否安装"""
    import platform
    import subprocess
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "Windows":
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]
    else:  # Linux
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            return True
    
    # 尝试通过命令行查找
    try:
        if system == "Darwin":
            subprocess.run(["which", "google-chrome"], check=True, capture_output=True)
        elif system == "Windows":
            subprocess.run(["where", "chrome"], check=True, capture_output=True)
        else:
            subprocess.run(["which", "google-chrome"], check=True, capture_output=True)
        return True
    except:
        pass
    
    return False

def ensure_chrome_driver():
    """确保ChromeDriver可用，返回ChromeDriver服务"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        import webdriver_manager
        from webdriver_manager.chrome import ChromeDriverManager
        
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 设置用户代理
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 获取ChromeDriver路径
        if getattr(sys, 'frozen', False):
            # 打包环境，使用内置的ChromeDriver
            driver_path = get_resource_path("chromedriver")
            if not os.path.exists(driver_path):
                raise FileNotFoundError(f"ChromeDriver not found at {driver_path}")
            service = Service(driver_path)
        else:
            # 开发环境，使用webdriver-manager自动管理
            service = Service(ChromeDriverManager().install())
        
        # 创建并返回ChromeDriver实例
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装selenium和webdriver-manager: pip install selenium webdriver-manager")
        return None
    except Exception as e:
        print(f"ChromeDriver初始化失败: {e}")
        return None

def setup_environment():
    """设置运行环境"""
    # 检查Chrome浏览器
    if not check_chrome_browser():
        print("警告: 未检测到Chrome浏览器，请确保已安装Google Chrome")
        print("下载地址: https://www.google.com/chrome/")
        return False
    
    # 设置临时目录用于存储媒体文件
    if getattr(sys, 'frozen', False):
        # 打包环境
        temp_dir = tempfile.mkdtemp(prefix="HotspotCrawler_")
        os.environ['HOTSPOT_CRAWLER_TEMP_DIR'] = temp_dir
        print(f"临时目录已创建: {temp_dir}")
    
    return True