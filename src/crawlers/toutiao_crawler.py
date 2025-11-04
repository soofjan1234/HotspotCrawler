
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 导入配置管理类
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 使用相对导入方式
from config.config_manager import ConfigManager
 
url = "https://www.toutiao.com/"
 
# 初始化配置管理器
config = ConfigManager()
# 确保必要的目录存在
config.ensure_directories()

options = Options()#创建一个 Options 类的实例 options，用于配置 Chrome 浏览器的启动选项。
# options.add_argument("--headless")  # 无界面模式
options.add_argument(f"user-agent={config.user_agent}")
#这里模拟了浏览器在当前系统上的请求，避免被网站识别为爬虫而限制访问。
 
 
driver = webdriver.Chrome(options=options)#创建一个 webdriver.Chrome 类的实例 driver，并将之前配置好的 options 传递给它
driver.get(url)#传入之前定义的 url 变量
time.sleep(3)  # 等待 JavaScript 执行
html = driver.page_source  # 获取渲染后的HTML
driver.quit() #关闭 Chrome 浏览器实例并释放相关资源。


# 使用正则表达式提取文章链接和标题
# 更新后的正则表达式更准确地匹配HTML结构
results = re.findall('<div class="feed-card-article-l"><a href="(.*?)".*?aria-label="(.*?)">', html, re.S)
print(f"\n共提取到 {len(results)} 条新闻")

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
        
        # 查找视频元素
        video_elements = soup.find_all('video')
        
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
max_articles = 3  # 最多处理3篇文章

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
    article_options.add_argument("--headless")  # 无界面模式
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
    article_media_dir = os.path.join(media_base_dir, f"{timestamp}_{safe_title[:8]}")
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
            # 创建文章的content.txt文件
            article_content_file = os.path.join(article_media_dir, 'content.txt')
            with open(article_content_file, 'w', encoding='utf-8') as article_f:
                article_f.write(f"第 {i+1} 条新闻\n")
                article_f.write(f"标题: {article_title}\n")
                article_f.write("正文内容: 未能提取到文章内容\n")
                article_f.write("\n" + "="*50 + "\n\n")
            print("未能提取到文章内容")
print(f"\n处理完成，共处理了 {processed_count} 篇新文章")
print(f"媒体文件已保存到: {media_base_dir}")
print(f"文章ID记录保存在: {article_id_file}")
