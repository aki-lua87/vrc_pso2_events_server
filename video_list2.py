import cv2
import glob
import os
import shutil
import time
import urllib.request
import json
import datetime
from PIL import Image,ImageFont, ImageDraw
import boto3
import base64

try:
    import unzip_requirements
except ImportError:
    pass

# メタ情報
frame_size = -1
frame_rate = 30.0
width = 1920
height = 1080
textRGB = (0, 0, 0)

# ローカル時にはプレフィックスに"."を付けてもろて
locate_setting = ''
imege_path = locate_setting+"/tmp/video.png"
video_path = locate_setting+"/tmp/video.mp4"
api_url = "https://vrc.akakitune87.net"

s3 = boto3.resource('s3')
s3_bucket = os.environ['S3_PUBLIC_BUCKET']

# Lambdaエントリポイント
def main(event, context):
    print(event)
    channel_id = event['path'].get('channel_id')
    # 実行時間計測
    start = time.time()

    # 画像を生成
    video_list = get_video_list(channel_id)
    s3_path = 'video.mp4'
    create_picture(channel_id,video_list)

    # 画像から動画を作成
    create_one_frame_video(imege_path,video_path)
    
    # 動画をS3に保存
    put_s3(s3_bucket,s3_path,video_path,user_id)

    # 実行時間出力
    elapsed_time = time.time() - start
    print ('{0}'.format(elapsed_time) + '[sec]')
    body = getLocalVideo()
    return base64.b64encode(body)


def create_one_frame_video(input_imege,output_video):
    # OpenCV設定
    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
    video = cv2.VideoWriter(output_video, fourcc, frame_rate, (width, height))
    
    # OpenCVでMP4描写
    img = cv2.imread(input_imege)
    img = cv2.resize(img,(width,height))

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

def put_s3(bucket_name,path,file,user_id):
    print('put_s3')
    bucket = s3.Bucket(bucket_name)
    bucket.upload_file(file, user_id+'/'+path)

def create_picture(user_id,video_list):
    image = Image.open('./images/template169.jpg')

    header1 = '現在のプレイリストの動画'

    line_pos = 5
    add_text_to_image(image,header1,'./font/f910-shin-comic-2.04.otf',75,textRGB,line_pos,125,20000)
    if len(video_list) == 0:
        print('[INFO] No Video data')
        return
    print(video_list)
    line_pos = line_pos + 20
    font_size = 34
    str_max_count = 62
    for i in range(len(video_list)):
        line_pos = line_pos + 50
        description = video_list[i]['description']
        text =  f'{i+1}: ' + description
        # 文字数が横枠超えそうなとき(かなり横着だけどこれ以上越えるのはもう知らん)
        if len(text) > str_max_count:
            add_text_to_image(image,text[:str_max_count],'./font/f910-shin-comic-2.04.otf',font_size,textRGB,line_pos,90,20000)
            line_pos = line_pos + 35
            add_text_to_image(image,'    '+text[str_max_count:],'./font/f910-shin-comic-2.04.otf',font_size,textRGB,line_pos,95,20000)
            continue
        add_text_to_image(image,text,'./font/f910-shin-comic-2.04.otf',font_size,textRGB,line_pos,90,20000)

    # 画像を保存
    image.save(imege_path)

def get_video_list(user_id):
    path = f'/users/{user_id}/video/all'
    url = api_url +path
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        body = res.read().decode('utf-8')
    print(body)
    return json.loads(body)

def getLocalVideo():
    with open(video_path, 'rb') as f:
        res= f.read()
    return res

def getS3Video(path,bucket_name):
    print('getS3Video',path,bucket_name)
    bucket = s3.Bucket(bucket_name)
    obj = bucket.Object(path)
    response = obj.get()    
    body = response['Body'].read()
    return body

def GetVideoList(channel_id):
    response = table.get_item(
        Key={
            'user_id': 'list_yt_ch',
            'video_id': f'{channel_id}',
        }
    )
    record = response.get('Item')
    if record == None:
        return None
    return record