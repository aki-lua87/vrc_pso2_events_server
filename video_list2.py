import os
import time
from PIL import Image, ImageFont, ImageDraw
import boto3
import base64
import cv2

# メタ情報
frame_size = -1
frame_rate = 20.0
width = 1920
height = 1080
textRGB = (0, 0, 0)

# ローカル時にはプレフィックスに"."を付けてもろて
locate_setting = ''
local_imege_path = locate_setting+"/tmp/video.png"
local_video_path = locate_setting+"/tmp/video.mp4"
api_url = "https://vrc.akakitune87.net"

s3 = boto3.resource('s3')
s3_bucket = os.environ['S3_PUBLIC_BUCKET']
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['VRC_VIDEO_TABLE'])

# 'yt/channel/'+channel_id+'.mp4'

# Lambdaエントリポイント


def main(event, context):
    print(event)
    channel_id = event['path'].get('channel_id')
    # 実行時間計測
    start = time.time()

    # Video取得
    videos = getVideoURLList(channel_id)

    # 画像を生成
    create_picture(videos)

    # 画像から動画を作成
    create_one_frame_video(local_imege_path, local_video_path)

    # 動画をS3に保存
    body = getLocalVideo(local_video_path)
    put_s3(s3_bucket, local_video_path, 'yt/channel/'+channel_id+'.mp4')

    # 実行時間出力
    elapsed_time = time.time() - start
    print('{0}'.format(elapsed_time) + '[sec]')
    return base64.b64encode(body)


def create_one_frame_video(input_imege, output_video):
    # OpenCV設定
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    video = cv2.VideoWriter(output_video, fourcc, frame_rate, (width, height))

    for idx in range(300):
        # イメージデータの領域確保
        img = cv2.imread(input_imege)
        img = cv2.resize(img, (width, height))
        video.write(img)

    # OpenCVでMP4描写
    img = cv2.imread(input_imege)
    img = cv2.resize(img, (width, height))

    # ローカルに書き込み
    video.write(img)
    video.release()


# 画像に文字を入れる関数
def add_text_to_image(img, text, font_path, font_size, font_color, height, width, max_length=1000):
    position = (width, height)
    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(img)
    if draw.textsize(text, font=font)[0] > max_length:
        while draw.textsize(text + '…', font=font)[0] > max_length:
            text = text[:-1]
        text = text + '…'
    draw.text(position, text, font_color, font=font)
    return img


def put_s3(bucket_name, local_file_path, s3_path):
    print('put_s3')
    bucket = s3.Bucket(bucket_name)
    bucket.upload_file(local_file_path, s3_path)


def create_picture(video_list):
    image = Image.open('./images/template169.jpg')

    header1 = '現在のプレイリストの動画'

    line_pos = 5
    add_text_to_image(image, header1, './font/f910-shin-comic-2.04.otf',
                      75, textRGB, line_pos, 125, 20000)
    if len(video_list) == 0:
        print('[INFO] No Video data')
        return
    print(video_list)
    line_pos = line_pos + 20
    font_size = 34
    str_max_count = 62
    for i in range(len(video_list)):
        line_pos = line_pos + 50
        titles = video_list[i]['titles']
        text = f'{i+1}: ' + titles
        # 文字数が横枠超えそうなとき(かなり横着だけどこれ以上越えるのはもう知らん)
        if len(text) > str_max_count:
            add_text_to_image(
                image, text[:str_max_count], './font/f910-shin-comic-2.04.otf', font_size, textRGB, line_pos, 90, 20000)
            line_pos = line_pos + 35
            add_text_to_image(
                image, '    '+text[str_max_count:], './font/f910-shin-comic-2.04.otf', font_size, textRGB, line_pos, 95, 20000)
            continue
        add_text_to_image(image, text, './font/f910-shin-comic-2.04.otf',
                          font_size, textRGB, line_pos, 90, 20000)

    # 画像を保存
    image.save(local_imege_path)


def getLocalVideo(path):
    with open(path, 'rb') as f:
        res = f.read()
    return res


def GetVideoList(channel_id):
    response = table.get_item(
        Key={
            'user_id': 'list_yt_ch',
            'video_id': f'{channel_id}',
        }
    )
    record = response.get('Item')
    if record is None:
        return None
    return record

# channel動画一覧を取得


def getVideoURLList(channel_id):
    # Videoのlistを取得
    v_list = GetVideoList(channel_id)
    if v_list is None:
        return None
    res = []
    for i in range(len(v_list['urls'])):
        res.append({'urls': v_list['urls'][i],
                    'titles': v_list['titles'][i]})
    return res
