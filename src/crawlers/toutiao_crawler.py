from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 添加项目根目录到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置管理器
from config.config_manager import ConfigManager

# 通用函数：从HTML中提取未爬取的文章
def extract_uncrawled_article(html, channel_name, crawled_ids, is_homepage=False):
    # 提取所有可能的文章匹配项（包括两种格式）
    all_matches = []
    
    # 只有在首页时才执行five-item的正则匹配
    if is_homepage:
        five_item_matches = re.findall('<div class="five-item"><i.*?</i><a href="(.*?)".*?aria-label="(.*?)">', html, re.S)
        all_matches.extend(five_item_matches)
    
    # 执行feed-card-article-l的正则匹配
    article_matches = re.findall('<div class="feed-card-article-l"><a href="(.*?)".*?aria-label="(.*?)">', html, re.S)
    all_matches.extend(article_matches)
    
    print(f"{channel_name} 频道提取到 {len(all_matches)} 篇文章")
    
    # 遍历所有文章，找到第一个未爬取的文章
    for i, match in enumerate(all_matches):
        article_relative_url = match[0]
        article_title = match[1]
        
        if article_relative_url.startswith('https://'):
            article_url = article_relative_url
        else:
            article_url = 'https://www.toutiao.com' + article_relative_url
        
        # 从URL中提取文章ID - 能处理完整URL和相对URL
        if is_homepage:
            # 首页的URL是完整的，直接从article_url中提取
            article_id_match = re.search(r'/article/(\d+)/', article_url)
        else:
            # 频道页面的URL是相对的，从article_relative_url中提取
            article_id_match = re.search(r'/article/(\d+)/', article_relative_url)
        if article_id_match:
            article_id = article_id_match.group(1)
            
            # 检查文章是否已爬取
            if article_id in crawled_ids:
                print(f"文章 {article_id} ({article_title}) 已爬取过，尝试提取 {channel_name} 频道的下一篇文章")
                continue  # 继续尝试下一篇文章
            else:
                print(f"找到 {channel_name} 频道第{i+1}篇未爬取的文章: {article_title}")
                print(f"文章URL: {article_url}")
                if is_homepage:
                    # 首页返回不同格式
                    return article_url, article_title, True
                else:
                    # 普通频道返回
                    return article_title, article_url
        else:
            print(f"无法从URL中提取文章ID: {article_url}，尝试下一篇")
    
    # 如果所有文章都已爬取过
    print(f"{channel_name} 频道所有文章都已爬取过")
    if is_homepage:
        # 首页返回空结果
        return None, None, False
    else:
        # 普通频道返回
        return None, None

# 点击导航项并提取文章标题的函数（支持重复时自动提取同板块下一篇）
def click_nav_item_and_extract_title(driver, nav_items, index, channel_name, crawled_ids):
    try:
        if index >= len(nav_items):
            print(f"警告: 索引 {index} 超出了导航项列表范围（共 {len(nav_items)} 个）")
            return None, None
        
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
        
        # 使用通用函数提取未爬取的文章 - 注意：此处is_homepage为False，返回值是(title, url)
        article_title, article_url = extract_uncrawled_article(html, channel_name, crawled_ids, is_homepage=False)
        return article_title, article_url
    except Exception as e:
        print(f"操作 {channel_name} 频道时发生错误: {e}")
        return None, None

# 头条首页URL
url = "https://www.toutiao.com/"

# 创建配置管理器实例
config = ConfigManager()

# 确保必要的目录存在
config.ensure_directories()

# 创建Chrome浏览器配置
options = Options()#创建一个 Options 类的实例 options，用于配置 Chrome 浏览器的启动选项。
# options.add_argument("--headless")  # 无界面模式
options.add_argument("--log-level=3")  # 只显示严重错误
options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁止日志输出
options.add_experimental_option('useAutomationExtension', False)
options.add_argument(f"user-agent={config.user_agent}")
# 存储所有频道的文章信息
all_channel_articles = []

# 获取配置的路径
media_base_dir = config.media_base_dir

# 使用配置管理器中的文章ID记录文件路径
article_id_file = config.article_id_file

# 函数：读取已爬取的文章ID
def read_article_ids():
    article_ids = set()
    try:
        if os.path.exists(article_id_file):
            # 检查文件最后修改时间，两周前的记录需要清理
            file_mod_time = os.path.getmtime(article_id_file)
            two_weeks_ago = (datetime.now() - timedelta(days=14)).timestamp()
            
            with open(article_id_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        article_id, timestamp = parts
                        # 只保留两周内的记录
                        if float(timestamp) >= two_weeks_ago:
                            article_ids.add(article_id)
            
            # 如果清理了旧记录，需要更新文件
            if len(article_ids) < len(open(article_id_file, 'r').readlines()):
                with open(article_id_file, 'w', encoding='utf-8') as f:
                    current_timestamp = str(time.time())
                    for article_id in article_ids:
                        f.write(f"{article_id},{current_timestamp}\n")
    except Exception as e:
        print(f"读取文章ID文件时出错: {str(e)}")
    return article_ids

# 函数：保存文章ID到文件
def save_article_id(article_id):
    try:
        with open(article_id_file, 'a', encoding='utf-8') as f:
            timestamp = str(time.time())
            f.write(f"{article_id},{timestamp}\n")
    except Exception as e:
        print(f"保存文章ID时出错: {str(e)}")

# 读取已爬取的文章ID（先读取，然后在提取阶段就进行重复检查）
crawled_ids = read_article_ids()
print(f"已爬取的文章ID数量: {len(crawled_ids)}")

try:
    # 创建浏览器实例
    driver = webdriver.Chrome(options=options)#创建一个 webdriver.Chrome 类的实例 driver，并将之前配置好的 options 传递给它
    
    # 访问头条网站
    print(f"正在访问: {url}")
    driver.get(url)
    time.sleep(5)  # 等待页面完全加载
    
    # 步骤1：在首页找到今日要闻（推荐频道）
    print("\n步骤1: 在首页查找今日要闻...")
    try:
        # 查找今日要闻区域
        html = driver.page_source
        
        # 使用通用函数提取首页未爬取的文章
        article_url, article_title, found_homepage_article = extract_uncrawled_article(html, "今日要闻", crawled_ids, is_homepage=True)
        
        if found_homepage_article and article_url and article_title:
            all_channel_articles.append(("今日要闻", article_url, article_title))
        else:
            print(f"首页今日要闻无未爬取文章")
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
        
        # 定义要点击的导航项索引和名称
        nav_to_click = [
            (2, "城市相关"),
            (4, "财经"),
            (5, "科技"),
            (6, "热点")
        ]
        
        # 依次点击各个导航项并提取文章（支持重复时自动切换到同板块下一篇）
        for index, channel_name in nav_to_click:
            # 传递crawled_ids参数给函数，使其能够在提取时进行判重
            title, article_url = click_nav_item_and_extract_title(driver, nav_items, index, channel_name, crawled_ids)
            if title and article_url:
                all_channel_articles.append((channel_name, article_url, title))
            else:
                print(f"{channel_name} 频道未能找到未爬取的文章")
    except Exception as e:
        print(f"操作导航项时发生错误: {e}")
    
    finally:
        # 关闭浏览器
        print("\n关闭浏览器...")
        driver.quit()
        
    # 显示所有频道的文章信息
    print("\n===== 所有频道文章汇总 =====")
    for i, (channel, url, title) in enumerate(all_channel_articles):
        print(f"{i+1}. {channel}: {title}")
        print(f"   URL: {url}")
    print(f"\n共获取到 {len(all_channel_articles)} 个频道的文章")
    
    # 准备处理这些文章（转换为原有格式）
    results = []
    for channel, article_url, article_title in all_channel_articles:
        # 提取相对URL用于文章ID提取
        match = re.search(r'https://www\.toutiao\.com(.*?)$', article_url)
        if match:
            relative_url = match.group(1)
            results.append((relative_url, f"[{channel}] {article_title}"))
    
    print(f"共准备处理 {len(results)} 条新闻")

except Exception as e:
    print(f"发生错误: {e}")

# 定义提取文章内容的函数
def extract_content_with_bs(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # 移除脚本和样式标签
    for script in soup(['script', 'style']):
        script.extract()
    # 提取文本
    text = soup.get_text()
    # 去除多余的空白字符
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

# 定义下载图片的函数
def download_images(image_urls, save_dir):
    downloaded_images = []
    for i, img_url in enumerate(image_urls):
        try:
            # 确保URL是完整的
            if not img_url.startswith(('http://', 'https://')):
                # 头条图片通常使用//开头，需要补充协议
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                else:
                    continue
            
            # 获取图片扩展名
            img_ext = img_url.split('.')[-1].split('?')[0]  # 获取扩展名，去掉可能的查询参数
            if len(img_ext) > 5:  # 如果扩展名太长，可能不是真的扩展名
                img_ext = 'jpg'
            
            # 保存图片
            img_name = f"image_{i + 1}.{img_ext}"
            img_path = os.path.join(save_dir, img_name)
            
            # 下载图片
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                downloaded_images.append(img_path)
                print(f"  已下载图片 {i + 1}/{len(image_urls)}")
            time.sleep(1)  # 避免请求过快
        except Exception as e:
            print(f"  下载图片失败: {str(e)}")
    return downloaded_images

# 定义提取并下载视频的函数
def extract_and_download_videos(html_content, save_dir):
    downloaded_videos = []
    try:
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        video_elements = soup.find_all('video')
            
        print(f"找到 {len(video_elements)} 个视频元素")
        
        for i, video in enumerate(video_elements):
            try:
                # 获取视频源URL
                video_url = None
                if video.get('src'):
                    video_url = video.get('src')
                else:
                    # 查找source标签
                    source = video.find('source')
                    if source and source.get('src'):
                        video_url = source.get('src')
                
                # 如果找不到直接的视频URL，尝试查找data-src或其他可能的属性
                if not video_url:
                    video_url = video.get('data-src') or video.get('data-video-url')
                
                # 还可以尝试通过正则表达式查找视频URL
                if not video_url:
                    video_match = re.search(r'videoUrl[\\s]*:[\\s]*["\'](.*?)["\']', html_content, re.S)
                    if video_match:
                        video_url = video_match.group(1)
                
                if video_url:
                    # 确保URL是完整的
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    elif not video_url.startswith(('http://', 'https://')):
                        continue
                    
                    # 保存视频
                    video_name = f"video_{i + 1}.mp4"  # 假设视频都是mp4格式
                    video_path = os.path.join(save_dir, video_name)
                    
                    print(f"  正在下载视频 {i + 1}/{len(video_elements)}")
                    # 下载视频（注意：视频文件可能很大，这里简化处理）
                    response = requests.get(video_url, stream=True, timeout=30)
                    if response.status_code == 200:
                        with open(video_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                                if chunk:
                                    f.write(chunk)
                        downloaded_videos.append(video_path)
                        print(f"  视频下载完成")
                time.sleep(2)  # 视频下载间隔更长一些
            except Exception as e:
                print(f"  下载视频失败: {str(e)}")
    except Exception as e:
        print(f"  提取视频信息失败: {str(e)}")
    return downloaded_videos

# 获取配置的路径
media_base_dir = config.media_base_dir

# 使用配置管理器中的文章ID记录文件路径
article_id_file = config.article_id_file

# 函数：读取已爬取的文章ID
def read_article_ids():
    article_ids = set()
    try:
        if os.path.exists(article_id_file):
            # 检查文件最后修改时间，两周前的记录需要清理
            file_mod_time = os.path.getmtime(article_id_file)
            two_weeks_ago = (datetime.now() - timedelta(days=14)).timestamp()
            
            with open(article_id_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        article_id, timestamp = parts
                        # 只保留两周内的记录
                        if float(timestamp) >= two_weeks_ago:
                            article_ids.add(article_id)
            
            # 如果清理了旧记录，需要更新文件
            if len(article_ids) < len(open(article_id_file, 'r').readlines()):
                with open(article_id_file, 'w', encoding='utf-8') as f:
                    current_timestamp = str(time.time())
                    for article_id in article_ids:
                        f.write(f"{article_id},{current_timestamp}\n")
    except Exception as e:
        print(f"读取文章ID文件时出错: {str(e)}")
    return article_ids

# 函数：保存文章ID到文件
def save_article_id(article_id):
    try:
        with open(article_id_file, 'a', encoding='utf-8') as f:
            timestamp = str(time.time())
            f.write(f"{article_id},{timestamp}\n")
    except Exception as e:
        print(f"保存文章ID时出错: {str(e)}")

# 读取已爬取的文章ID
crawled_ids = read_article_ids()
print(f"已爬取的文章ID数量: {len(crawled_ids)}")

# 处理每个文章
processed_count = 0
max_articles = 1  # 最多处理1篇文章

for i, result in enumerate(results):
    if processed_count >= max_articles:
        break
        
    article_relative_url = result[0]
    article_url = 'https://www.toutiao.com' + article_relative_url
    article_title = result[1]
    
    # 从URL中提取文章ID
    article_id_match = re.search(r'/article/(\d+)/', article_relative_url)
    if not article_id_match:
        print(f"无法从URL中提取文章ID: {article_url}")
        continue
    
    article_id = article_id_match.group(1)
    
    # 检查是否已爬取过该文章
    if article_id in crawled_ids:
        print(f"文章 {article_id} 已爬取过，跳过")
        continue
    
    processed_count += 1
    print(f"\n正在处理第 {processed_count} 条新闻:")
    print(f"标题: {article_title}")
    print(f"URL: {article_url}")
    print(f"文章ID: {article_id}")
    
    # 创建新的浏览器实例访问文章详情页
    article_options = Options()
    # article_options.add_argument("--headless")  # 无界面模式
    article_options.add_argument(f"user-agent={config.user_agent}")
    
    article_driver = webdriver.Chrome(options=article_options)
    article_driver.get(article_url)
    time.sleep(3)  # 等待页面加载
    
    article_html = article_driver.page_source
    article_driver.quit()
    
    # 创建该文章的媒体保存目录
    # 清理标题，去除不能作为文件名的字符
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', article_title)
    # 使用时间戳_标题前8个字的格式命名文件夹
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    article_media_dir = os.path.join(media_base_dir, f"{timestamp}_{safe_title[:16]}")
    os.makedirs(article_media_dir, exist_ok=True)
    
    # 保存文章ID到文件
    save_article_id(article_id)
        
    # 尝试找到文章内容区域
    content_match = re.search(r'syl-device-pc">(.*?)</article>', article_html, re.S)
    if content_match:
        article_content_html = content_match.group(1)
        # 使用BeautifulSoup提取纯文本内容
        article_text = extract_content_with_bs(article_content_html)
        
        # 提取并下载图片
        print(f"  开始提取图片...")
        soup = BeautifulSoup(article_content_html, 'html.parser')
        img_tags = soup.find_all('img')
        img_urls = [img.get('src') for img in img_tags if img.get('src')]
        # 还可以尝试获取其他可能的图片属性
        data_src_urls = [img.get('data-src') for img in img_tags if img.get('data-src')]
        img_urls.extend(data_src_urls)
        
        # 去重
        img_urls = list(set(img_urls))
        print(f"  找到 {len(img_urls)} 张图片")
        
        # 创建图片保存子目录
        image_dir = os.path.join(article_media_dir, 'images')
        os.makedirs(image_dir, exist_ok=True)
        downloaded_images = download_images(img_urls, image_dir)
        
        # 提取并下载视频
        print(f"  开始提取视频...")
        video_dir = os.path.join(article_media_dir, 'videos')
        os.makedirs(video_dir, exist_ok=True)
        downloaded_videos = extract_and_download_videos(article_content_html, video_dir)
        
        # 创建文章的content.txt文件
        article_content_file = os.path.join(article_media_dir, 'content.txt')
        with open(article_content_file, 'w', encoding='utf-8') as article_f:
            article_f.write(f"第 {i+1} 条新闻\n")
            article_f.write(f"标题: {article_title}\n")
            article_f.write("正文内容:\n")
            article_f.write(article_text)
            
            # 写入媒体文件信息
            # article_f.write(f"\n媒体文件信息:\n")
            # article_f.write(f"  图片数量: {len(downloaded_images)}\n")
            # for img_path in downloaded_images:
            #     # 保存相对路径
            #     rel_img_path = os.path.relpath(img_path, article_media_dir)
            #     article_f.write(f"  - {rel_img_path}\n")
            
            # article_f.write(f"  视频数量: {len(downloaded_videos)}\n")
            # for video_path in downloaded_videos:
            #     # 保存相对路径
            #     rel_video_path = os.path.relpath(video_path, article_media_dir)
            #     article_f.write(f"  - {rel_video_path}\n")
            
            # article_f.write("\n" + "="*50 + "\n\n")
        
        print(f"文章内容已提取，长度: {len(article_text)} 字符")
        print(f"图片下载完成，共 {len(downloaded_images)} 张")
        print(f"视频下载完成，共 {len(downloaded_videos)} 个")
    else:
        print("未能提取到文章内容")
print(f"\n处理完成，共处理了 {processed_count} 篇新文章")
print(f"媒体文件已保存到: {media_base_dir}")
print(f"文章ID记录保存在: {article_id_file}")
