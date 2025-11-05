from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
import os
import sys
import random

# 添加项目根目录到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入配置管理器
from config.config_manager import ConfigManager

# 导入模块化的类
from crawlers.article_extractor import ArticleExtractor
from crawlers.media_downloader import MediaDownloader
from crawlers.article_manager import ArticleManager
from datetime import datetime

class ToutiaoCrawler:
    """头条爬虫主类"""
    
    def __init__(self):
        # 创建配置管理器实例
        self.config = ConfigManager()
        
        # 确保必要的目录存在
        self.config.ensure_directories()
        
        # 获取配置的路径
        self.media_base_dir = self.config.media_base_dir
        self.article_id_file = self.config.article_id_file
        
        # 头条首页URL
        self.url = "https://www.toutiao.com/"
        
        # 初始化各模块
        self.article_extractor = ArticleExtractor()
        self.media_downloader = MediaDownloader()
        self.article_manager = ArticleManager(self.article_id_file)
        
        # 存储所有频道的文章信息
        self.all_channel_articles = []
        
        # 创建Chrome浏览器配置
        self.options = Options()
        # self.options.add_argument("--headless")  # 无界面模式
        self.options.add_argument("--log-level=3")  # 只显示严重错误
        self.options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁止日志输出
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument(f"user-agent={self.config.user_agent}")
        
        # 定义频道列表
        self.channels = ["今日要闻", "城市相关", "财经", "科技", "热点"]
        
        # 生成各频道的文章分配比例
        self.article_allocation = self.generate_article_allocation()
    
    def generate_article_allocation(self):
        """生成各频道的文章分配比例
        
        随机生成5个正整数，总和为10，确保分布均匀
        """
        # 所有频道列表
        all_channels = ["今日要闻", "城市相关", "财经", "科技", "热点"]
        
        # 首先给每个频道分配至少1篇，确保每个频道都有文章
        allocation = {channel: 1 for channel in all_channels}
        remaining = 10 - len(all_channels)  # 10 - 5 = 5篇剩余
        
        # 使用加权随机分配剩余文章，权重基于当前分配数量的倒数
        # 这样可以确保分配更少的频道有更高概率获得额外文章
        for _ in range(remaining):
            # 计算权重：当前分配越少，权重越高
            weights = [1 / allocation[channel] for channel in all_channels]
            
            # 根据权重选择一个频道
            selected_channel = random.choices(all_channels, weights=weights, k=1)[0]
            
            # 给选中的频道增加1篇
            allocation[selected_channel] += 1
        
        print(f"优化后的文章分配方案: {allocation}")
        return allocation
    
    def crawl_homepage(self):
        """爬取首页内容，按照分配比例获取文章"""
        print("\n步骤1: 在首页查找今日要闻...")
        try:
            # 获取今日要闻的分配数量
            need_count = self.article_allocation.get("今日要闻", 1)
            print(f"需要从今日要闻获取 {need_count} 篇文章")
            
            # 查找今日要闻区域
            html = self.driver.page_source
            
            # 保存已处理的文章ID，避免重复
            processed_ids = set()
            collected_count = 0
            
            # 尝试获取指定数量的文章
            for _ in range(need_count * 3):  # 多尝试几次以确保能获取足够数量
                # 使用通用函数提取首页未爬取的文章
                article_url, article_title, found_homepage_article = self.article_extractor.extract_uncrawled_article(
                    html, "今日要闻", self.crawled_ids.union(processed_ids), is_homepage=True
                )
                
                if found_homepage_article and article_url and article_title:
                    # 提取文章ID
                    article_id_match = re.search(r'/article/(\d+)/', article_url)
                    if article_id_match:
                        article_id = article_id_match.group(1)
                        processed_ids.add(article_id)
                        self.all_channel_articles.append(("今日要闻", article_url, article_title))
                        collected_count += 1
                        # print(f"已添加首页文章: {article_title}")
                        
                        # 如果达到需要的数量，停止收集
                        if collected_count >= need_count:
                            break
                
                # 短暂休眠避免请求过快
                time.sleep(0.5)
                
            print(f"今日要闻文章收集完成，共 {collected_count} 篇")
            
        except Exception as e:
            print(f"查找今日要闻时发生错误: {e}")
    
    def crawl_channels(self):
        """爬取各个频道，按照分配比例获取文章"""
        print("\n正在查找div.feed-default-nav-item元素...")
        
        try:
            # 查找所有具有feed-default-nav-item类的div元素
            nav_items = self.driver.find_elements(By.CLASS_NAME, "feed-default-nav-item")
            
            # 定义要点击的导航项索引和名称
            nav_to_click = [
                (2, "城市相关"),
                (4, "财经"),
                (5, "科技"),
                (6, "热点")
            ]
            
            # 依次点击各个导航项并按照分配比例提取文章
            for index, channel_name in nav_to_click:
                # 获取当前频道的分配数量
                need_count = self.article_allocation.get(channel_name, 2)
                print(f"\n正在处理 {channel_name} 频道，需要获取 {need_count} 篇文章...")
                
                # 保存当前频道已处理的文章ID，避免重复
                processed_ids = set()
                collected_count = 0
                
                # 点击频道
                try:
                    target_item = nav_items[index]
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target_item)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", target_item)
                    time.sleep(3)  # 等待页面加载
                except Exception as e:
                    print(f"点击 {channel_name} 频道失败: {e}")
                    continue
                
                # 尝试从当前频道获取指定数量的文章
                for i in range(need_count * 3):  # 多尝试几次以确保能获取足够数量
                    html = self.driver.page_source
                    title, article_url = self.article_extractor.extract_uncrawled_article(
                        html, channel_name, self.crawled_ids.union(processed_ids), is_homepage=False
                    )
                    
                    if title and article_url:
                        # 提取文章ID
                        article_id_match = re.search(r'/article/(\d+)/', article_url)
                        if article_id_match:
                            article_id = article_id_match.group(1)
                            processed_ids.add(article_id)
                            self.all_channel_articles.append((channel_name, article_url, title))
                            collected_count += 1
                            # print(f"已添加{channel_name}频道文章 {collected_count}: {title}")
                            
                            # 如果达到需要的数量，停止收集
                            if collected_count >= need_count:
                                break
                        
                        # 滚动页面加载更多文章
                        self.driver.execute_script("window.scrollBy(0, 800);")
                        time.sleep(2)
                    else:
                        # 如果没找到文章，滚动更多
                        self.driver.execute_script("window.scrollBy(0, 1000);")
                        time.sleep(3)
                
                print(f"{channel_name}频道文章收集完成，共 {collected_count} 篇")
                
        except Exception as e:
            print(f"操作导航项时发生错误: {e}")
    
    def process_articles(self):
        """处理爬取到的文章"""
        # 显示所有频道的文章信息
        print("\n===== 所有频道文章汇总 =====")
        for i, (channel, url, title) in enumerate(self.all_channel_articles):
            print(f"{i+1}. {channel}: {title}")
            print(f"   URL: {url}")
        print(f"\n共获取到 {len(self.all_channel_articles)} 篇文章")
        
        # 按频道统计文章数量
        channel_counts = {}
        for channel, _, _ in self.all_channel_articles:
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        print(f"文章分布: {', '.join([f'{ch}: {count}篇' for ch, count in channel_counts.items()])}")
        
        # 准备处理这些文章（转换为原有格式）
        results = []
        for channel, article_url, article_title in self.all_channel_articles:
            # 提取相对URL用于文章ID提取
            match = re.search(r'https://www\.toutiao\.com(.*?)$', article_url)
            if match:
                relative_url = match.group(1)
                results.append((relative_url, f"[{channel}] {article_title}"))
        
        print(f"\n准备处理 {len(results)} 条新闻")
        
        processed_count = 0
        max_articles = len(results)  # 处理所有收集到的文章
        
        for i, result in enumerate(results):
            if processed_count >= max_articles:
                break
            
            article_relative_url = result[0]
            article_url = 'https://www.toutiao.com' + article_relative_url
            article_title = result[1]
            
            article_id_match = re.search(r'/article/(\d+)/', article_relative_url)
            if not article_id_match:
                print(f"无法从URL中提取文章ID: {article_url}")
                continue
            
            article_id = article_id_match.group(1)
            
            if article_id in self.crawled_ids:
                print(f"文章 {article_id} 已爬取过，跳过")
                continue
            
            processed_count += 1
            print(f"\n正在处理第 {processed_count} 条新闻:")
            print(f"标题: {article_title}")
            print(f"URL: {article_url}")
            print(f"文章ID: {article_id}")
            
            # 创建文章页面的浏览器配置
            article_options = Options()
            article_options.add_argument("--log-level=3")
            article_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            article_options.add_argument(f"user-agent={self.config.user_agent}")
            
            # 打开文章页面
            article_driver = webdriver.Chrome(options=article_options)
            article_driver.get(article_url)
            time.sleep(3)  # 等待页面加载
            
            # 获取文章HTML
            article_html = article_driver.page_source
            article_driver.quit()
            
            # 创建安全的文件名
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', article_title)
            
            # 创建保存目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            article_media_dir = os.path.join(self.media_base_dir, f"{timestamp}_{safe_title[:16]}")
            os.makedirs(article_media_dir, exist_ok=True)
            
            # 保存文章ID
            self.article_manager.save_article_id(article_id)
            
            # 提取文章内容
            content_match = re.search(r'syl-device-pc">(.*?)</article>', article_html, re.S)
            if content_match:
                article_content_html = content_match.group(1)
                
                # 提取文本内容
                article_text = self.article_extractor.extract_content_with_bs(article_content_html)
                
                # 提取并下载图片
                print(f"  开始提取图片...")
                soup = BeautifulSoup(article_content_html, 'html.parser')
                img_tags = soup.find_all('img')
                img_urls = [img.get('src') for img in img_tags if img.get('src')]
                
                # 尝试获取data-src属性（懒加载图片）
                data_src_urls = [img.get('data-src') for img in img_tags if img.get('data-src')]
                img_urls.extend(data_src_urls)
                
                # 去重
                img_urls = list(set(img_urls))
                print(f"  找到 {len(img_urls)} 张图片")
                
                # 创建图片目录并下载
                image_dir = os.path.join(article_media_dir, 'images')
                os.makedirs(image_dir, exist_ok=True)
                downloaded_images = self.media_downloader.download_images(img_urls, image_dir)
                
                # 提取并下载视频
                print(f"  开始提取视频...")
                video_dir = os.path.join(article_media_dir, 'videos')
                os.makedirs(video_dir, exist_ok=True)
                downloaded_videos = self.media_downloader.extract_and_download_videos(article_content_html, video_dir)
                
                # 保存文章内容到文件
                article_content_file = os.path.join(article_media_dir, 'content.txt')
                with open(article_content_file, 'w', encoding='utf-8') as article_f:
                    article_f.write(f"第 {i+1} 条新闻\n")
                    article_f.write(f"标题: {article_title}\n")
                    article_f.write("正文内容:\n")
                    article_f.write(article_text)
                
                # 显示处理结果
                print(f"文章内容已提取，长度: {len(article_text)} 字符")
                print(f"图片下载完成，共 {len(downloaded_images)} 张")
                print(f"视频下载完成，共 {len(downloaded_videos)} 个")
            else:
                print("未能提取到文章内容")
        
        print(f"\n处理完成，共处理了 {processed_count} 篇新文章")
        print(f"媒体文件已保存到: {self.media_base_dir}")
        print(f"文章ID记录保存在: {self.article_id_file}")
    

        
    def run(self):
        """运行爬虫主流程"""
        # 读取已爬取的文章ID
        self.crawled_ids = self.article_manager.read_article_ids()
        print(f"已爬取的文章ID数量: {len(self.crawled_ids)}")
        
        try:
            # 创建浏览器实例
            self.driver = webdriver.Chrome(options=self.options)
            
            # 访问头条网站
            print(f"正在访问: {self.url}")
            self.driver.get(self.url)
            time.sleep(5)  # 等待页面完全加载
            
            # 爬取首页
            self.crawl_homepage()
            
            # 爬取各频道
            self.crawl_channels()
            
        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            # 关闭浏览器
            if hasattr(self, 'driver'):
                print("\n关闭浏览器...")
                self.driver.quit()
        
        # 处理文章
        if self.all_channel_articles:
            self.process_articles()

# 如果直接运行此文件，执行爬虫
if __name__ == "__main__":
    # 导入必要的模块
    from bs4 import BeautifulSoup
    
    # 创建并运行爬虫
    crawler = ToutiaoCrawler()
    crawler.run()