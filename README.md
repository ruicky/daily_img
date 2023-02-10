# Daily Img

> 生成每日一图，包含天气，日期。

![](doc/weather.jpg)

接口：
`http://<ip>:80/api/weather`

## INSTALL

### With git clone

```shell
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CITY="北京"
export WEATHER_KEY="XXXXXX"

# Run
uvicorn main:app --reload
```
其中 `WEATHER_KEY` 为和风天气的 key，可以在 https://dev.heweather.com/ 申请。

### With Docker
```shell
docker run -d --name=Daily-Img --restart=unless-stopped \
-e CITY="北京" \
-e WEATHER_KEY="XXXXXX" \
ruicky/daily_img:latest
```