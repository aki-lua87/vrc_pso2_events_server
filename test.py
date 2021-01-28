import cv2
import glob
import os
import shutil
import time
import urllib.request
import json
import datetime
from PIL import Image,ImageFont, ImageDraw

# メタ情報
frame_size = -1
frame_rate = 30.0
width = 1080
height = 1920
textRGB = (0, 0, 0)

# 本日の緊急クエストを取得しdictで返す
def get_pso2_events():
    # 今日の日付を取得
    today = datetime.date.today()
    today_yyyymmdd = str(today.year) + str(today.month).zfill(2) + str(today.day).zfill(2)
    print("today_yyyymmdd:",today_yyyymmdd)

    url = 'https://pso2.akakitune87.net/api/emergency'
    data = {
        "EventDate":today_yyyymmdd,
    }
    headers = {
        'Content-Type': 'application/json',
    }
    req = urllib.request.Request(url, json.dumps(data).encode(), headers)
    with urllib.request.urlopen(req) as res:
        body = res.read().decode("utf-8")
    return json.loads(body)

def careate_one_frame_video(images):
    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
    video = cv2.VideoWriter('pso2events.mp4', fourcc, frame_rate, (width, height))
    
    print("aaaaa")
    events_data = get_pso2_events()
    print(events_data)
    
    for i in range(len(images)):
        # テキスト挿入
        image = Image.open(images[i])
        header = str(events_data[0]['Month']) + "/" + str(events_data[0]['Date']) + "の緊急クエスト"
        add_text_to_image(image,header,"./font/f910-shin-comic-2.04.otf",56,textRGB,0,20,20000)
        for i in range(len(events_data)):
            time = str(events_data[i]['Hour']).zfill(2) + ":" + str(events_data[i]['Minute']).zfill(2)
            event_name = events_data[i]['EventName']
            text = time + "       " + event_name
            add_text_to_image(image,text,"./font/f910-shin-comic-2.04.otf",56,textRGB,60*(i+1),100,20000)
        image.save("pso2events.png")

        # OpenCVでMP4描写
        img = cv2.imread("pso2events.png")
        img = cv2.resize(img,(width,height))

        video.write(img) 
    video.release()
    print("bbbb")

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

if __name__ == '__main__':
    start = time.time()
    
    images = sorted(glob.glob('images/*.jpg'))
    print("{0}".format(len(images)))
    careate_one_frame_video(images)

    elapsed_time = time.time() - start
    print ("{0}".format(elapsed_time) + "[sec]")


