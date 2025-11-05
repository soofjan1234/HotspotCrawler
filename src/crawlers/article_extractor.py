from bs4 import BeautifulSoup
import re
import time

class ArticleExtractor:
    """文章内容提取器类"""
    
    def extract_uncrawled_article(self, html, channel_name, crawled_ids, is_homepage=False):
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
                    # print(f"文章 {article_id} ({article_title}) 已爬取过，尝试提取 {channel_name} 频道的下一篇文章")
                    continue  # 继续尝试下一篇文章
                else:
                    # print(f"找到 {channel_name} 频道第{i+1}篇未爬取的文章: {article_title}")
                    # print(f"文章URL: {article_url}")
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
    
    def extract_content_with_bs(self, html_content):
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
    
    def click_nav_item_and_extract_title(self, driver, nav_items, index, channel_name, crawled_ids):
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
            article_title, article_url = self.extract_uncrawled_article(html, channel_name, crawled_ids, is_homepage=False)
            return article_title, article_url
        except Exception as e:
            print(f"操作 {channel_name} 频道时发生错误: {e}")
            return None, None