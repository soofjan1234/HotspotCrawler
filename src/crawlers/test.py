from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import sys
import re

# 导入配置管理类
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_manager import ConfigManager

# 初始化配置管理器
config = ConfigManager()

print("开始实现多频道切换功能...")

# 设置Chrome选项
options = Options()
# options.add_argument("--headless")  # 无界面模式，可注释掉以查看浏览器操作
options.add_argument(f"user-agent={config.user_agent}")

# 创建浏览器实例
driver = webdriver.Chrome(options=options)

# 提取文章标题的函数
def extract_first_article_title(html, is_recommend_module=False):
    # 如果是推荐模块，则先提取今日要闻格式（格式2）
    if is_recommend_module:
        # 格式2：five-item 中的 aria-label（今日要闻格式）
        results2 = re.findall('<div class="five-item"><i.*?</i><a.*?aria-label="(.*?)">', html, re.S)
        if results2:
            return results2[0]
    
    # 格式1：feed-card-article-l 中的 aria-label
    results1 = re.findall('<div class="feed-card-article-l"><a href=".*?".*?aria-label="(.*?)">', html, re.S)
    if results1:
        return results1[0]
    
    
    
    
    return "未找到文章标题"

# 点击导航项并提取第一篇文章标题的函数
def click_nav_item_and_extract_title(driver, nav_items, index, channel_name):
    try:
        if index >= len(nav_items):
            print(f"警告: 索引 {index} 超出了导航项列表范围（共 {len(nav_items)} 个）")
            return None
        
        target_item = nav_items[index]
        print(f"\n准备点击第 {index+1} 个导航项: {channel_name} (索引: {index})")
        
        # 获取点击前的文本（用于确认）
        item_text = target_item.text.strip()
        print(f"导航项文本: {item_text}")
        
        # 确保元素在可视区域内
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target_item)
        time.sleep(1)
        
        # 使用JavaScript点击该元素
        print(f"使用JavaScript点击 {channel_name} 导航项...")
        driver.execute_script("arguments[0].click();", target_item)
        print(f"{channel_name} 导航项点击成功")
        
        # 等待页面切换和加载
        time.sleep(3)
        
        # 获取页面内容
        html = driver.page_source
        
        # 提取第一篇文章标题（非推荐模块）
        title = extract_first_article_title(html, is_recommend_module=False)
        print(f"{channel_name} 频道第一篇文章标题: {title}")
        
        return title
    except Exception as e:
        print(f"操作 {channel_name} 频道时发生错误: {e}")
        return None

try:
    # 访问头条网站
    url = "https://www.toutiao.com/"
    print(f"正在访问: {url}")
    driver.get(url)
    time.sleep(3)  # 等待页面加载
    
    # 步骤1：在首页找到今日要闻
    print("\n步骤1: 在首页查找今日要闻...")
    try:
        # 查找今日要闻区域
        html = driver.page_source
        
        # 提取今日要闻的第一篇文章标题（首页是推荐模块）
        news_title = extract_first_article_title(html, is_recommend_module=True)
        print(f"首页今日要闻第一篇文章标题: {news_title}")
        
        # 尝试直接查找feed-five-wrapper（今日要闻区域）
        today_news_section = driver.find_elements(By.CLASS_NAME, "feed-five-wrapper")
        if today_news_section:
            print("成功找到今日要闻区域")
    except Exception as e:
        print(f"查找今日要闻时发生错误: {e}")
    
    # 步骤2-5：查找导航项并执行切换
    print("\n正在查找div.feed-default-nav-item元素...")
    
    try:
        # 查找所有具有feed-default-nav-item类的div元素
        nav_items = driver.find_elements(By.CLASS_NAME, "feed-default-nav-item")
        print(f"找到 {len(nav_items)} 个feed-default-nav-item元素")
        
        # 打印所有导航项文本，用于调试
        print("导航项列表:")
        for i, item in enumerate(nav_items):
            print(f"{i}: {item.text.strip()}")
        
        # 步骤2：点击第三个导航项（城市相关）
        city_title = click_nav_item_and_extract_title(driver, nav_items, 2, "城市相关")
        
        # 步骤3：点击第五个导航项（财经）
        finance_title = click_nav_item_and_extract_title(driver, nav_items, 4, "财经")
        
        # 步骤4：点击第六个导航项（科技）
        tech_title = click_nav_item_and_extract_title(driver, nav_items, 5, "科技")
        
        # 步骤5：点击第七个导航项（热点）
        hot_title = click_nav_item_and_extract_title(driver, nav_items, 6, "热点")
        
        # 汇总结果
        print("\n===== 提取结果汇总 =====")
        print(f"首页今日要闻第一篇文章标题: {news_title}")
        print(f"城市相关频道第一篇文章标题: {city_title}")
        print(f"财经频道第一篇文章标题: {finance_title}")
        print(f"科技频道第一篇文章标题: {tech_title}")
        print(f"热点频道第一篇文章标题: {hot_title}")
    
        
    except Exception as e:
        print(f"操作导航项时发生错误: {e}")
        
    
finally:
    # 关闭浏览器
    print("\n关闭浏览器...")
    driver.quit()
    print("多频道切换测试完成")