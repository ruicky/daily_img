import requests
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime
import time
from zhdate import ZhDate
import re
from PIL import Image, ImageDraw, ImageFont
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

city = os.getenv('CITY', '北京')
key = os.getenv('WEATHER_KEY')

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
_LOGGER = logging.getLogger(__name__)


# 请求天气数据
def get_weather():
    # city = "北京"
    city_url = "https://geoapi.qweather.com/v2/city/lookup?location=" + city + "&key=" + key
    response_city = session.request("GET", city_url, timeout=30)
    city_data = response_city.json()
    # _LOGGER.error(f'city_data:{city_data}')
    daily_weather_iconDay = '100'
    if city_data['code'] == '200':
        city_data = city_data["location"][0]
        city_name = city_data["name"]
        city_id = city_data["id"]
        weather_url = "https://devapi.qweather.com/v7/weather/3d?location=" + city_id + "&key=" + key
        response = session.request("GET", weather_url, timeout=30)
        weather_data = response.json()
        if weather_data['code'] == '200':
            daily_weather_data = weather_data["daily"][0]
            daily_weather_iconDay = daily_weather_data["iconDay"]
            daily_weather_desc = daily_weather_data["textDay"]
            daily_weather_tempMin = daily_weather_data["tempMin"]
            daily_weather_tempMax = daily_weather_data["tempMax"]
            cond = f'{daily_weather_desc}  {daily_weather_tempMin}°~{daily_weather_tempMax}°'
        else:
            cond = '风雨难测°'
            _LOGGER.error(f'获取天气信息失败')
    else:
        city_name = '你在天涯海角'
        cond = '风雨难测°'
        _LOGGER.error(
            f'获取城市名失败,请确定 ➊【城市名称】是否设置正确，示例：北京。➋【和风天气】的 key 设置正确')
        _LOGGER.error(
            f'【和风天气】的 KEY 在 https://dev.qweather.com 申请，创建项目后进入控制台新建项目然后添加 KEY')
        _LOGGER.error(
            f'在项目管理找到新建的项目，KEY 下面有个查看，点开查看，即可查看需要填入到插件的 API KEY 值')

    return city_name, cond, daily_weather_iconDay

# 获取当天星期
def get_weekday():
    week_day_dict = {
        0: '一',
        1: '二',
        2: '三',
        3: '四',
        4: '五',
        5: '六',
        6: '日',
    }
    date = datetime.now()
    day = date.weekday()
    weekday = week_day_dict[day]
    return weekday

# 获取当天日期
def get_date():
    today = time.strftime("%Y-%m", time.localtime())
    today_day = time.strftime("%d", time.localtime())
    today_month = time.strftime("%m", time.localtime())
    today_year = time.strftime("%Y", time.localtime())
    return today,today_day,today_month,today_year

# 获取当天农历
def get_lunar_date(today_day,today_month,today_year):
    solar_date = datetime(int(today_year), int(today_month), int(today_day)) # 新建一个阳历日期
    solar_to_lunar_date = ZhDate.from_datetime(solar_date)  # 阳历日期转换农历日期
    # 输出中文农历日期
    lunar_date = solar_to_lunar_date.chinese()
    # 二零二二年三月初一 壬寅年 (虎年)提取三月初一
    lunar_date = re.search(r'年(.*?) ', lunar_date)
    if lunar_date:
        lunar_date = lunar_date.group(1)
    else:
        lunar_date = ''
    return lunar_date

# 获取心灵鸡汤
def get_quote():
    quote_url = 'https://v1.hitokoto.cn'
    quote = session.request("GET", quote_url, timeout=30)
    response = quote.json()
    quote_content = response['hitokoto']
    line_length = 21
    lines = []
    for i in range(0, len(quote_content), line_length):
        lines.append(quote_content[i:i + line_length])
    if len(lines) > 2:
        lines[1] = lines[1][:-1] + "..."
    quote_content = '\n'.join(lines[:2])
    return quote_content

def process_weather_data(daily_weather_iconDay):
    daily_weather_iconDay = int(daily_weather_iconDay)
    # Define colors
    today_day_color = (252, 215, 102)
    line_color = (255, 255, 255, 50)
    weekday_color = (255, 255, 255)
    today_color = (255, 255, 255)
    lunar_date_color = (255, 255, 255)
    quote_content_color = (255, 255, 255, 150)
    icon_color = (255, 255, 255)
    city_color = (255, 255, 255)
    weather_desc_color = (255, 255, 255)
    # Set colors for fog, haze, and dust
    if daily_weather_iconDay in [500,501,509,510,514,515,502,511,512,513]:
        today_day_color = (169, 67, 56)
        line_color = (72, 63, 61, 50)
        weekday_color = (72, 63, 61)
        today_color = (72, 63, 61)
        lunar_date_color = (72, 63, 61)
        quote_content_color = (72, 63, 61, 150)
        icon_color = (72, 63, 61)
        city_color = (72, 63, 61)
        weather_desc_color = (72, 63, 61)
    # Define unicode values and background names
    default_weather_values = (hex(0xf1ca), 'sunny')
    weather_data = {
        99999:  default_weather_values,
        100:  (hex(0xf1cc), 'sunny'),
        101:  (hex(0xf1cd), 'cloud'),
        102:  (hex(0xf1ce), 'cloud'),
        103:  (hex(0xf1cf), 'cloud'),
        104:  (hex(0xf1d0), 'cloud'),
        300:  (hex(0xf1d5), 'rain'),
        301:  (hex(0xf1d6), 'rain'),
        302:  (hex(0xf1d7), 'rain'),
        303:  (hex(0xf1d8), 'rain'),
        304:  (hex(0xf1d9), 'rain'),
        305:  (hex(0xf1da), 'rain'),
        306:  (hex(0xf1db), 'rain'),
        307:  (hex(0xf1dc), 'rain'),
        308:  (hex(0xf1dd), 'rain'),
        309:  (hex(0xf1de), 'rain'),
        310:  (hex(0xf1df), 'rain'),
        311:  (hex(0xf1e0), 'rain'),
        312:  (hex(0xf1e1), 'rain'),
        313:  (hex(0xf1e2), 'rain'),
        314:  (hex(0xf1e3), 'rain'),
        315:  (hex(0xf1e4), 'rain'),
        316:  (hex(0xf1e5), 'rain'),
        317:  (hex(0xf1e6), 'rain'),
        318:  (hex(0xf1e7), 'rain'),
        399:  (hex(0xf1ea), 'rain'),
        400:  (hex(0xf1eb), 'snow'),
        401:  (hex(0xf1ec), 'snow'),
        402:  (hex(0xf1ed), 'snow'),
        403:  (hex(0xf1ee), 'snow'),
        404:  (hex(0xf1ef), 'snow'),
        405:  (hex(0xf1f0), 'snow'),
        406:  (hex(0xf1f1), 'snow'),
        407:  (hex(0xf1f2), 'snow'),
        408:  (hex(0xf1f3), 'snow'),
        409:  (hex(0xf1f4), 'snow'),
        410:  (hex(0xf1f5), 'snow'),
        499:  (hex(0xf1f8), 'snow'),
        500:  (hex(0xf1f9), 'fog'),
        501:  (hex(0xf1fa), 'fog'),
        502:  (hex(0xf1fb), 'haze'),
        503:  (hex(0xf1fc), 'dust'),
        504:  (hex(0xf1fd), 'dust'),
        507:  (hex(0xf1fe), 'dust'),
        508:  (hex(0xf1ff), 'dust'),
        509:  (hex(0xf200), 'haze'),
        510:  (hex(0xf201), 'haze'),
        511:  (hex(0xf202), 'haze'),
        512:  (hex(0xf203), 'haze'),
        513:  (hex(0xf204), 'haze'),
        514:  (hex(0xf205), 'fog'),
        515:  (hex(0xf206), 'fog')
    }
    bg_name = weather_data.get(daily_weather_iconDay, default_weather_values)[1]
    unicode_value = weather_data.get(daily_weather_iconDay, default_weather_values)[0]
    # bg_name, unicode_value = weather_data.get(daily_weather_iconDay, default_weather_values)
    unicode_text = chr(int(unicode_value, 16))
    return bg_name,unicode_text,today_day_color,line_color,weekday_color,today_color,lunar_date_color,quote_content_color,icon_color,city_color,weather_desc_color

# 生成图片
def generate_image(img_prefix):
    # 画布大小
    width = 1500
    height = 640
    weekday = get_weekday()
    # 获取天气数据
    city_name, cond, daily_weather_iconDay = get_weather()
    today, today_day, today_month, today_year = get_date()
    lunar_date = get_lunar_date(today_day, today_month, today_year)
    quote_content = get_quote()
    bg_name, unicode_text, today_day_color, line_color, weekday_color, today_color, lunar_date_color, quote_content_color, icon_color, city_color, weather_desc_color = process_weather_data(
        daily_weather_iconDay)

    # 加载图片
    bg = Image.open(f"./bg/{bg_name}.png")

    # 创建画布
    image = Image.new("RGBA", (width, height), (0, 0, 255, 0))
    square = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    # suqredraw = ImageDraw.Draw(square)

    # 绘制天气背景，覆盖整个画布
    square.paste(bg, (0, 0), mask=bg)

    # 加载字体
    icon_font = ImageFont.truetype(f"./font/qweather-icons.ttf", 85)
    num_font_Bold = ImageFont.truetype(f"./font/ALIBABA_Bold.otf", 345)
    num_font_Regular = ImageFont.truetype(f"./font/ALIBABA_Regular.otf", 62)
    week_font_Regular = ImageFont.truetype(f"./font/zh.ttf", 140)
    text_font = ImageFont.truetype(f"./font/syht.otf", 53)
    quote_font = ImageFont.truetype(f"./font/syht.otf", 60)

    day_x = 85
    day_y = 35
    # 绘制日期
    draw.text((day_x, day_y), today_day, fill=today_day_color, font=num_font_Bold, align='center')
    # today_day_width, today_day_height = draw.textsize(today_day, num_font_Bold)
    # 获取文字宽度
    today_day_width = draw.textlength(today_day, num_font_Bold)

    # 绘制竖线
    # 定义线段的起始坐标和终止坐标
    x0, y0 = day_x + today_day_width + 25, day_y + 118
    x1, y1 = x0, y0 + 210

    # 绘制白色线段，宽度为4
    draw.line((x0, y0, x1, y1), fill=line_color, width=4)

    # 绘制星期
    draw.text((day_x + today_day_width + 80, day_y + 95), '星', fill=weekday_color, font=week_font_Regular)
    draw.text((day_x + today_day_width + 80 + 120 + 20, day_y + 95), '期', fill=weekday_color, font=week_font_Regular)
    draw.text((day_x + today_day_width + 80 + 120 + 130 + 20, day_y + 95), weekday, fill=weekday_color,
              font=week_font_Regular)
    # 绘制年月
    year_month_width = draw.textlength(today, num_font_Regular)
    draw.text((day_x + today_day_width + 80, day_y + 270), today, fill=today_color, font=num_font_Regular)
    draw.text((day_x + today_day_width + 80 + year_month_width + 20, day_y + 270), lunar_date, fill=lunar_date_color,
              font=text_font)

    # 绘制鸡汤
    draw.text((day_x + 20, day_y + 400), quote_content, fill=quote_content_color, font=quote_font)

    # 绘制天气图标
    icon_width = draw.textlength(unicode_text, icon_font)
    draw.text((width - 105 - icon_width, day_y + 100), unicode_text, fill=icon_color, font=icon_font, align='center')

    # 绘制城市
    city_width = draw.textlength(city_name, text_font)
    draw.text((width - 105 - city_width, day_y + 195), city_name, fill=city_color, font=text_font)
    # 绘制天气说明
    cond_width = draw.textlength(cond, text_font)
    draw.text((width - 105 - cond_width + 18, day_y + 270), cond, fill=weather_desc_color, font=text_font)
    # 保存图片
    image1 = Image.alpha_composite(square, image)
    # image1.save(f"./weather.png")
    image1 = image1.convert("RGB")
    image1.save(f"./{img_prefix}weather.jpg", quality=97)
    # shutil.copy(f'./weather.png', f'./weather.jpg')
    # image_path = f'./weather.png'
    image_path = f'static/weather.jpg'
    try:
        if not os.path.exists(image_path):
            image_path = f'./logo.jpg'
    except Exception as e:
        _LOGGER.error(f'检查文件是否存在时发生异常，原因：{e}')


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/weather")
def getWeatherImg():
    # 当前时间，格式为20230210
    img_prefix = datetime.now().strftime('%Y%m%d')
    img_name = img_prefix + 'weather.jpg'
    # 删除除了img_name之外的文件名包含 weather.jpg 的文件
    for file in os.listdir('./'):
        if file != img_name and 'weather.jpg' in file:
            os.remove(file)
    # 判断文件是否存在
    if not os.path.exists(img_name):
        generate_image(img_prefix)

    def iterfile():  # (1)
        with open(f'./{img_name}', mode="rb") as file_like:
            yield from file_like  # (3)
    return StreamingResponse(iterfile(), media_type="image/jpeg")