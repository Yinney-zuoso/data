import requests
import time
import pandas as pd
import os
from datetime import datetime, timedelta, time as dt_time
from dotenv import load_dotenv

# 加载 .env 配置文件
load_dotenv()

# --- 配置信息 ---
MY_AMAP_KEY = os.getenv("AMAP_KEY", "")
DONGGUAN_CITY_NAME = os.getenv("DONGGUAN_CITY_NAME", "东莞")
API_DOMAIN = "https://restapi.amap.com/v3/weather/weatherInfo"

# 采集间隔
INTERVAL_MINUTES = int(os.getenv("WEATHER_COLLECTION_INTERVAL_MINUTES", "10"))

# *** 采集时间窗口配置（可选）***
# 如果 .env 中没有配置时间窗口，则不使用时间窗口限制
WEATHER_START_YEAR = int(os.getenv("WEATHER_START_YEAR", "0"))
WEATHER_START_MONTH = int(os.getenv("WEATHER_START_MONTH", "0"))
WEATHER_START_DAY = int(os.getenv("WEATHER_START_DAY", "0"))
WEATHER_START_HOUR = int(os.getenv("WEATHER_START_HOUR", "0"))
WEATHER_START_MINUTE = int(os.getenv("WEATHER_START_MINUTE", "0"))
WEATHER_START_SECOND = int(os.getenv("WEATHER_START_SECOND", "0"))

WEATHER_END_YEAR = int(os.getenv("WEATHER_END_YEAR", "0"))
WEATHER_END_MONTH = int(os.getenv("WEATHER_END_MONTH", "0"))
WEATHER_END_DAY = int(os.getenv("WEATHER_END_DAY", "0"))
WEATHER_END_HOUR = int(os.getenv("WEATHER_END_HOUR", "0"))
WEATHER_END_MINUTE = int(os.getenv("WEATHER_END_MINUTE", "0"))
WEATHER_END_SECOND = int(os.getenv("WEATHER_END_SECOND", "0"))

# 数据保存目录和文件名
DATA_DIR = "data"
TIMESTAMP_STR = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILENAME = os.path.join(DATA_DIR, f"weather_data_{TIMESTAMP_STR}.csv")


def get_realtime_weather(city_name, key):
    """ 调用高德天气 API 获取实时天气数据 """
    url = f"{API_DOMAIN}"
    params = {
        "city": city_name,
        "key": key,
        "extensions": "base" # 请求实时天气数据
    }

    if not key or not city_name:
        return {"error": "配置错误：API Key 或城市名称不能为空。"}

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get('infocode') == '10000' and data.get('lives'):
            live_data = data['lives'][0]
            return {
                "weather_phenomenon": live_data.get('weather'),      # 天气现象
                "temperature_C": live_data.get('temperature'),       # 温度
                "wind_direction": live_data.get('winddirection'),    # 风向
                "wind_power": live_data.get('windpower')             # 风力
            }
        else:
            error_code = data.get('infocode', '未知')
            error_msg = data.get('info', '未知错误')
            return {"error": f"API业务错误: {error_code} - {error_msg}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"网络请求失败: {e}"}
    except Exception as e:
        return {"error": f"数据处理错误: {e}"}


def run_continuous_collection():

    # 检查是否配置了时间窗口
    has_time_window = all([WEATHER_START_YEAR, WEATHER_START_MONTH, WEATHER_START_DAY])

    # 创建数据目录
    os.makedirs(DATA_DIR, exist_ok=True)

    if has_time_window:
        # 配置了时间窗口
        try:
            START_DT = datetime(WEATHER_START_YEAR, WEATHER_START_MONTH, WEATHER_START_DAY, WEATHER_START_HOUR, WEATHER_START_MINUTE, WEATHER_START_SECOND)
            END_DT = datetime(WEATHER_END_YEAR, WEATHER_END_MONTH, WEATHER_END_DAY, WEATHER_END_HOUR, WEATHER_END_MINUTE, WEATHER_END_SECOND)
        except ValueError as e:
            print(f"⚠️ 警告: 日期或时间配置错误: {e}。任务中止。")
            return

        now = datetime.now()

        # 检查任务时间窗口是否合理
        if END_DT <= START_DT:
            print(f"⚠️ 错误: 结束时间 ({END_DT}) 必须晚于开始时间 ({START_DT})。任务中止。")
            return
        if now > END_DT:
            print(f"⚠️ 警告: 目标结束时间 {END_DT.strftime('%Y-%m-%d %H:%M')} 已过，任务无法执行。")
            return

        total_duration_hours = (END_DT - START_DT).total_seconds() / 3600

        print(f"--- 🚀 任务启动 (高德平台 / 北京时间) ---")
        print(f"  当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  城市: {DONGGUAN_CITY_NAME}")
        print(f"  采集时间窗口: **{START_DT.strftime('%Y-%m-%d %H:%M:%S')}** 到 **{END_DT.strftime('%Y-%m-%d %H:%M:%S')}**")
        print(f"  持续时间: 约 {round(total_duration_hours / 24, 1)} 天")
        print(f"  采集间隔: **{INTERVAL_MINUTES} 分钟**")
        print(f"  预计总调用次数：约 **{int((END_DT - START_DT).total_seconds() / (INTERVAL_MINUTES * 60))}** 次")
        print(f"  **数据将输出到文件: {OUTPUT_FILENAME}**\n")

        # 写入 CSV 文件头部 (新建文件)
        df_header = pd.DataFrame([{"Timestamp": "", "Weather": "", "Temp_C": "", "Wind_Dir": "", "Wind_Power": "", "Status": ""}]).drop(0)
        df_header.to_csv(OUTPUT_FILENAME, index=False, encoding='utf_8_sig')

        # 初始化下一个目标采集时间
        next_target_time = datetime.now()  # 从当前时间开始
        collection_count = 0
        interval_seconds = INTERVAL_MINUTES * 60

        while datetime.now() <= END_DT:

            # 确保在目标时间点采集
            wait_to_target = (next_target_time - datetime.now()).total_seconds()
            if wait_to_target > 0:
                time.sleep(wait_to_target)
                current_dt = next_target_time
            else:
                # 不补录，直接使用当前时间
                current_dt = datetime.now()

            timestamp_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
            loop_start_time = time.time()
            collection_count += 1

            print(f"\n[+] [{collection_count}] 正在采集... 记录时间: {timestamp_str}")

            weather_data = get_realtime_weather(DONGGUAN_CITY_NAME, MY_AMAP_KEY)

            # 记录和输出结果
            if "error" in weather_data:
                status = weather_data['error']
                print(f"  -> 失败。返回信息: {status}")
                record = {"Timestamp": timestamp_str, "Weather": "FAIL", "Temp_C": "FAIL", "Wind_Dir": "FAIL", "Wind_Power": "FAIL", "Status": status}
            else:
                status = "Success"
                print(f"  -> 结果: 天气 **{weather_data['weather_phenomenon']}**, 温度 **{weather_data['temperature_C']}°C**")
                record = {"Timestamp": timestamp_str, "Weather": weather_data['weather_phenomenon'], "Temp_C": weather_data['temperature_C'], "Wind_Dir": weather_data['wind_direction'], "Wind_Power": weather_data['wind_power'], "Status": status}

            # 写入文件（追加模式）
            new_df = pd.DataFrame([record])
            new_df.to_csv(OUTPUT_FILENAME, mode='a', header=False, index=False, encoding='utf_8_sig')

            print(f"  -> 记录已保存到 {OUTPUT_FILENAME}")

            # 更新下一个目标采集时间
            next_target_time += timedelta(seconds=interval_seconds)

            if next_target_time > END_DT:
                print("\n--- 采集即将完成，下一个目标时间超出结束时间 ---")
                break

            # 打印等待信息
            time_spent_on_call = time.time() - loop_start_time
            remaining_wait = (next_target_time - datetime.now()).total_seconds()

            if remaining_wait > 0:
                print(f"--- API耗时 {round(time_spent_on_call, 2)}s。等待 {round(remaining_wait, 2)} 秒。下一次采集预计在 {next_target_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
            else:
                print(f"--- 警告: 采集耗时 {round(time_spent_on_call, 2)}s，超过了 {INTERVAL_MINUTES} 分钟的间隔。立即进入下一轮采集。---")

    else:
        # 没有配置时间窗口，直接启动，持续运行
        print(f"--- 🚀 任务启动 (无时间窗口限制) ---")
        print(f"  当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  城市: {DONGGUAN_CITY_NAME}")
        print(f"  采集间隔: **{INTERVAL_MINUTES} 分钟**")
        print(f"  **数据将输出到文件: {OUTPUT_FILENAME}**\n")

        # 写入 CSV 文件头部
        df_header = pd.DataFrame([{"Timestamp": "", "Weather": "", "Temp_C": "", "Wind_Dir": "", "Wind_Power": "", "Status": ""}]).drop(0)
        df_header.to_csv(OUTPUT_FILENAME, index=False, encoding='utf_8_sig')

        collection_count = 0
        next_target_time = datetime.now()
        interval_seconds = INTERVAL_MINUTES * 60

        try:
            while True:
                # 确保在目标时间点采集
                wait_to_target = (next_target_time - datetime.now()).total_seconds()
                if wait_to_target > 0:
                    time.sleep(wait_to_target)
                    current_dt = next_target_time
                else:
                    # 不补录，直接使用当前时间
                    current_dt = datetime.now()

                timestamp_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
                loop_start_time = time.time()
                collection_count += 1

                print(f"\n[+] [{collection_count}] 正在采集... 记录时间: {timestamp_str}")

                weather_data = get_realtime_weather(DONGGUAN_CITY_NAME, MY_AMAP_KEY)

                # 记录和输出结果
                if "error" in weather_data:
                    status = weather_data['error']
                    print(f"  -> 失败。返回信息: {status}")
                    record = {"Timestamp": timestamp_str, "Weather": "FAIL", "Temp_C": "FAIL", "Wind_Dir": "FAIL", "Wind_Power": "FAIL", "Status": status}
                else:
                    status = "Success"
                    print(f"  -> 结果: 天气 **{weather_data['weather_phenomenon']}**, 温度 **{weather_data['temperature_C']}°C**")
                    record = {"Timestamp": timestamp_str, "Weather": weather_data['weather_phenomenon'], "Temp_C": weather_data['temperature_C'], "Wind_Dir": weather_data['wind_direction'], "Wind_Power": weather_data['wind_power'], "Status": status}

                # 写入文件（追加模式）
                new_df = pd.DataFrame([record])
                new_df.to_csv(OUTPUT_FILENAME, mode='a', header=False, index=False, encoding='utf_8_sig')

                print(f"  -> 记录已保存到 {OUTPUT_FILENAME}")

                # 更新下一个目标采集时间
                next_target_time += timedelta(seconds=interval_seconds)

                # 打印等待信息
                time_spent_on_call = time.time() - loop_start_time
                remaining_wait = (next_target_time - datetime.now()).total_seconds()

                if remaining_wait > 0:
                    print(f"--- API耗时 {round(time_spent_on_call, 2)}s。等待 {round(remaining_wait, 2)} 秒。下一次采集预计在 {next_target_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
                else:
                    print(f"--- 警告: 采集耗时 {round(time_spent_on_call, 2)}s，超过了 {INTERVAL_MINUTES} 分钟的间隔。立即进入下一轮采集。---")
        except KeyboardInterrupt:
            print("\n--- ⏹️  用户中断任务 ---")

    print("\n--- ✅ 采集任务结束 ---")
    print(f"  共采集 {collection_count} 次数据，所有数据都在 {OUTPUT_FILENAME} 文件中。")


if __name__ == "__main__":
    run_continuous_collection()