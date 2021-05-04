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

# メタ情報
frame_size = -1
frame_rate = 30.0
width = 1000
height = 1500
textRGB = (0, 0, 0)

s3 = boto3.resource('s3')

s3_bucket = os.environ['S3_PUBLIC_BUCKET']
s3_path = 'pso2events.mp4'
imege_path = "/tmp/pso2events.png"
video_path = "/tmp/pso2events.mp4"

# Lambdaエントリポイント
def main(event, context):
    # 実行時間計測
    start = time.time()

    # 画像を生成
    create_picture()

    # 画像から動画を作成
    create_one_frame_video(imege_path,video_path)
    
    # 動画をS3に保存
    put_s3(s3_bucket,s3_path,video_path)

    # 実行時間出力
    elapsed_time = time.time() - start
    print ('{0}'.format(elapsed_time) + '[sec]')

# 本日の緊急クエストを取得しdictで返す
def get_pso2_events(yyyymmdd):
    url = 'https://pso2.akakitune87.net/api/emergency'
    data = {
        'EventDate':yyyymmdd,
        'EventType':'緊急'
    }
    headers = {
        'Content-Type': 'application/json',
    }
    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req) as res:
        body = res.read().decode('utf-8')
    return json.loads(body)

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

def put_s3(bucket_name,path,file):
    print('put_s3')
    bucket = s3.Bucket(bucket_name)
    bucket.upload_file(file, path)

def today_yyyymmdd():
    today = datetime.date.today()
    today_yyyymmdd = str(today.year) + str(today.month).zfill(2) + str(today.day).zfill(2)
    return today_yyyymmdd

def tommorow_yyyymmdd():
    tommorow = datetime.date.today() + datetime.timedelta(days = 1)
    tommorow_yyyymmdd = str(tommorow.year) + str(tommorow.month).zfill(2) + str(tommorow.day).zfill(2)
    return tommorow_yyyymmdd

def create_picture():
    image = Image.open('./images/template.jpg')

    header1 = 'PSO2緊急リスト'

    line_pos = 5
    add_text_to_image(image,header1,'./font/f910-shin-comic-2.04.otf',89,textRGB,line_pos,125,20000)

    events_data1 = get_pso2_events(today_yyyymmdd())
    events_data2 = get_pso2_events(tommorow_yyyymmdd())
    print(events_data1,events_data2)

    # 今日の緊急
    line_pos = line_pos + 150
    header2 = str(events_data1[0]['Month']) + '/' + str(events_data1[0]['Date']) + 'のイベント'
    add_text_to_image(image,header2,'./font/f910-shin-comic-2.04.otf',56,textRGB,line_pos,20,20000)
    
    for i in range(len(events_data1)):
        line_pos = line_pos + 60
        time = str(events_data1[i]['Hour']).zfill(2) + ':' + str(events_data1[i]['Minute']).zfill(2)
        event_name = events_data1[i]['EventName']
        text = time + '   ' + event_name
        add_text_to_image(image,text,'./font/f910-shin-comic-2.04.otf',56,textRGB,line_pos,100,20000)

    # 明日の緊急
    line_pos = line_pos + 150
    header3 = str(events_data2[0]['Month']) + '/' + str(events_data2[0]['Date']) + 'のイベント'
    add_text_to_image(image,header3,'./font/f910-shin-comic-2.04.otf',56,textRGB,line_pos,20,20000)
    
    for i in range(len(events_data2)):
        line_pos = line_pos + 60
        time = str(events_data2[i]['Hour']).zfill(2) + ':' + str(events_data2[i]['Minute']).zfill(2)
        event_name = events_data2[i]['EventName']
        text = time + '   ' + event_name
        add_text_to_image(image,text,'./font/f910-shin-comic-2.04.otf',56,textRGB,line_pos,100,20000)
    
    # 画像を保存
    image.save(imege_path)
