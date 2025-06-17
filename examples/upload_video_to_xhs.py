import configparser
from pathlib import Path
from time import sleep

from xhs import XhsClient
import sys
import os
# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from conf import BASE_DIR
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags
from uploader.xhs_uploader.main import sign_local, beauty_print

config = configparser.RawConfigParser()
config.read(Path(BASE_DIR / "uploader" / "xhs_uploader" / "accounts.ini"))

# 账号 cookie
# filePath

if __name__ == '__main__':
    # 从命令行参数获取视频目录和账号名
    import argparse
    parser = argparse.ArgumentParser(description='上传视频到小红书')
    parser.add_argument('account_name', help='账号名称')
    parser.add_argument('video_path', help='视频文件路径')
    parser.add_argument('-t', '--time', help='发布时间 (格式: YYYY-MM-DD HH:MM)')
    parser.add_argument('-pt', '--post_time', type=int, default=0, help='是否定时发布(0:立即发布, 1:定时发布)')
    args = parser.parse_args()

    # 获取视频文件
    filepath = Path(args.video_path)
    if not filepath.exists():
        print(f"视频文件不存在: {filepath}")
        exit(1)

    # 获取账号配置
    try:
        cookies = config[args.account_name]['cookies']
    except KeyError:
        print(f"账号 {args.account_name} 配置不存在")
        exit(1)

    xhs_client = XhsClient(cookies, sign=sign_local, timeout=60)
    # auth cookie
    try:
        xhs_client.get_video_first_frame_image_id("3214")
    except:
        print("cookie 失效")
        exit(1)

    # 获取标题和标签
    title, tags, game = get_title_and_hashtags(str(filepath))
    tags_str = ' '.join(['#' + tag for tag in tags])
    hash_tags_str = ''
    hash_tags = []

    # 打印视频文件名、标题和 hashtag
    print(f"视频文件名：{filepath}")
    print(f"标题：{title}")
    print(f"Hashtag：{tags}")

    topics = []
    # 获取hashtag
    for i in tags[:3]:
        topic_official = xhs_client.get_suggest_topic(i)
        if topic_official:
            topic_official[0]['type'] = 'topic'
            topic_one = topic_official[0]
            hash_tag_name = topic_one['name']
            hash_tags.append(hash_tag_name)
            topics.append(topic_one)

    hash_tags_str = ' ' + ' '.join(['#' + tag + '[话题]#' for tag in hash_tags])

    # 设置发布时间
    post_time = None
    if args.post_time == 1 and args.time:
        try:
            # 将时间字符串转换为datetime对象，然后格式化为所需的格式
            from datetime import datetime
            post_time = datetime.strptime(args.time, '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            print(f"时间格式错误: {e}")
            print("请使用正确的格式: YYYY-MM-DD HH:MM")
            exit(1)

    print(post_time)

    note = xhs_client.create_video_note(
        title=title[:20], 
        video_path=str(filepath),
        desc=tags_str + hash_tags_str,
        topics=topics,
        is_private=False,
        post_time=post_time
    )

    beauty_print(note)
    # 强制休眠30s，避免风控（必要）
    sleep(30)
