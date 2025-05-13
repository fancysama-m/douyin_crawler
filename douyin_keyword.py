import csv
import os
import re
import urllib.parse
from datetime import datetime
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json


def spider(text, num, cookie, uifid, msToken, a_bogus):
    result = []

    encoded = urllib.parse.quote(text, encoding="utf-8")
    h1 = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cookie': cookie,
        'referer': f'https://www.douyin.com/search/{encoded}?type=video',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'uifid': uifid
    }


    file_name = f"douyin_data_{text}.csv"
    # 如果存在文件
    index = 1


    for n in range(num):
        print(f"正在爬取第 {n + 1} 页数据")
        # 需要搜索的文本
        offset = n * 10


        # Douyin API URL
        douyin_url = f'https://www.douyin.com/aweme/v1/web/search/item/?device_platform=webapp&aid=6383&channel' \
                     f'=channel_pc_web&search_channel=aweme_video_web&enable_history=1&sort_type=0&publish_time=180' \
                     f'&keyword=' \
                     f'{encoded}&search_source=switch_tab&query_correct_type=1&is_filter_search=1&from_group_id=&offset=' \
                     f'{offset}&count=10&need_filter_settings=1&list_type=multi&update_version_code=170400' \
                     f'&pc_client_type=1&pc_libra_divert=Windows&support_h265=1&support_dash=1&cpu_core_num=20' \
                     f'&version_code=170400&version_name=17.4.0&cookie_enabled=true&screen_width=1536&screen_height' \
                     f'=864&browser_language=zh-CN&browser_platform=Win32&browser_name=Chrome&browser_version=136.0.0' \
                     f'.0&browser_online=true&engine_name=Blink&engine_version=136.0.0.0&os_name=Windows&os_version' \
                     f'=10&device_memory=8&platform=PC&downlink=10&effective_type=4g&round_trip_time=50&webid' \
                     f'=7501244975285585419&' \
                     f'uifid' \
                     f'={uifid}&version_code=190600&version_name=19.6.0&webid=7501244975285585419&' \
                     f'&msToken={msToken}' \
                     f'&a_bogus={a_bogus}'

        r = requests.get(douyin_url, headers=h1, timeout=(30, 30))

        def extract_json_objects(text):
            decoder = json.JSONDecoder()
            pos = 0
            length = len(text)
            results = []

            while pos < length:
                try:
                    # 尝试从当前位置解析一个 JSON 对象
                    obj, offset = decoder.raw_decode(text[pos:])
                    results.append(obj)
                    pos += offset
                except json.JSONDecodeError:
                    # 如果当前位置不是合法 JSON 开头，就跳过一个字符
                    pos += 1
            return results

        # 提取所有 JSON 对象
        all_aweme_infos = []
        try:
            json_objects = json.loads(r.text)['data']
            json_objects = json_objects
            for obj in json_objects:
                all_aweme_infos.append(obj['aweme_info'])
        except json.JSONDecodeError:
            json_objects = extract_json_objects(r.text)


            for obj in json_objects:
                if isinstance(obj, dict) and 'data' in obj:
                    for item in obj['data']:
                        if 'aweme_info' in item:
                            all_aweme_infos.append(item['aweme_info'])
        import time
        import random
        # 防检测
        time.sleep(random.uniform(3, 10))  # 随机延迟3~10秒

        # 解析 JSON 数据
        for data in all_aweme_infos:
            # aweme_info = data.get('aweme_info')
            if data is not None:
                aweme_id = data['aweme_id']
                idxs = []
                if os.path.exists(file_name):
                    df = pd.read_csv(file_name, encoding='utf-8')
                    idxs = df['视频id'].values.tolist()
                    index = len(df) + 1
                if int(aweme_id) in set(idxs):
                    print(f"跳过已存在的视频ID: {aweme_id}")
                    continue
                desc = data['desc'].replace("\n", "").replace("\r", "")
                create_time = datetime.utcfromtimestamp(data['create_time']).strftime("%Y-%m-%d %H:%M:%S")
                author_uid = data['author']['uid']
                nickname = data['author']['nickname']
                enterprise_verify_reason = data['author'].get('enterprise_verify_reason', '').replace("\n", "").replace("\r", "")
                collect_count = data['statistics']['collect_count']
                comment_count = data['statistics']['comment_count']
                digg_count = data['statistics']['digg_count']
                download_count = data['statistics']['download_count']
                share_count = data['statistics']['share_count']
                link = 'https://www.douyin.com/video/' + aweme_id
                with open(file_name, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f,
                                            fieldnames=['视频id', '链接', '标题', '创建时间', '创作者id', '创作者昵称',
                                                        '认证', '收藏量', '评论量', '点赞量', '下载量', '转发量'])
                    if f.tell() == 0:
                        writer.writeheader()

                    writer.writerow({
                        '视频id': aweme_id,
                        '链接': link,
                        '标题': desc,
                        '创建时间': create_time,
                        '创作者id': author_uid,
                        '创作者昵称': nickname,
                        '认证': enterprise_verify_reason,
                        '收藏量': collect_count,
                        '评论量': comment_count,
                        '点赞量': digg_count,
                        '下载量': download_count,
                        '转发量': share_count
                    })
                # result.append({
                #     '视频id': aweme_id,
                #     '链接': link,
                #     '标题': desc,
                #     '创建时间': create_time,
                #     '创作者id': author_uid,
                #     '创作者昵称': nickname,
                #     '认证': enterprise_verify_reason,
                #     '收藏量': collect_count,
                #     '评论量': comment_count,
                #     '点赞量': digg_count,
                #     '下载量': download_count,
                #     '转发量': share_count
                # })
                print(f"已爬取第 {index} 条数据", aweme_id, link, desc, create_time, author_uid, nickname,
                      enterprise_verify_reason, collect_count, comment_count, digg_count, download_count, share_count)
                index += 1
        time.sleep(2)

    #     # 将结果转换为 DataFrame
    # df = pd.DataFrame(result)
    # # 将 DataFrame 保存为 CSV 文件
    # df.to_csv('douyin_data.csv',  index=False)


if __name__ == '__main__':
    
    # 请求头, 对应复制粘贴
    cookie = ''
    uifid = ''
    msToken = ''
    a_bogus = ''
    
    # 标题
    text = "XXX"
    # 爬取的页数
    num = 2000
    for j in range(1, int(num/20 + 1)):
        # 调用爬虫函数
        spider(text, 20, cookie, uifid, msToken, a_bogus)
