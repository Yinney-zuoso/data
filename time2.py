import requests
import time
from datetime import datetime, timedelta

# --- 配置信息 ---
MY_AMAP_KEY = "XX"  # 请使用您自己的高德 Key
ORIGIN_COORDINATE = "113.8070,23.0450"      
DESTINATION_COORDINATE = "114.0150,22.8550" 
ROAD_SEGMENT_NAME = "石碣互通立交 - 塘厦立交"

# 采集间隔固定为 20 秒
COLLECTION_INTERVAL_SECONDS = 20 

# *** 采集时间窗口配置 ***
# 目标开始日期和时间：2026年1月1日 23:59:00 (北京时间)
START_YEAR = 2026
START_MONTH = 1
START_DAY = 1
START_HOUR = 23
START_MINUTE = 59
START_SECOND = 0

# 目标结束日期和时间：2026年2月1日 0:00:00 (北京时间)
END_YEAR = 2026
END_MONTH = 2
END_DAY = 1
END_HOUR = 0
END_MINUTE = 0
END_SECOND = 0
# *** 采集时间窗口配置结束 ***

# *** 修正点：将输出文件名修改为 "time2.csv" ***
OUTPUT_FILENAME = "time2.csv"


def get_fastest_driving_time(origin, destination, key):
    """
    调用高德驾车路径规划 API，获取实时行程时间。
    返回 (分钟数 float, 是否成功 bool)
    """
    url = "https://restapi.amap.com/v3/direction/driving"
    params = {
        "origin": origin,
        "destination": destination,
        "key": key,
        "extensions": "base",
        "output": "json",
        "strategy": 0 
    }

    if not all([origin, destination, key]):
        return "配置错误：起点、终点或 API Key 不能为空。", False

    try:
        # 请求超时设置为10秒
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  
        data = response.json()

        if data.get('status') == '1' and data.get('route') and data['route'].get('paths'):
            duration_seconds = int(data['route']['paths'][0]['duration'])
            duration_minutes = round(duration_seconds / 60, 2)
            return duration_minutes, True
        else:
            error_info = data.get('info', '未知错误')
            return f"API错误: {error_info}", False

    except requests.exceptions.RequestException as e:
        return f"网络请求失败: {e}", False
    except Exception as e:
        return f"数据处理错误: {e}", False

def run_timed_collection():
    
    # 设定目标开始时间和结束时间（使用明确的日期）
    try:
        target_start_time = datetime(START_YEAR, START_MONTH, START_DAY, START_HOUR, START_MINUTE, START_SECOND)
        target_end_time = datetime(END_YEAR, END_MONTH, END_DAY, END_HOUR, END_MINUTE, END_SECOND)
    except ValueError as e:
        print(f"⚠️ 警告: 日期或时间配置错误: {e}。任务中止。")
        return

    now = datetime.now()
    
    # 时间检查
    if target_end_time <= target_start_time:
        print("⚠️ 警告: 配置的开始时间晚于或等于结束时间。请检查配置。任务中止。")
        return
        
    if now > target_end_time:
         print(f"⚠️ 警告: 目标结束时间 {target_end_time.strftime('%Y-%m-%d %H:%M:%S')} 已过。任务中止。")
         return

    current_interval = COLLECTION_INTERVAL_SECONDS
    
    # 计算总时长用于信息展示
    total_duration_days = (target_end_time - target_start_time).total_seconds() / 86400

    print(f"--- 🚀 任务启动 ---")
    print(f"  当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  路段: {ROAD_SEGMENT_NAME}")
    print(f"  采集时间窗口: **{target_start_time.strftime('%Y-%m-%d %H:%M:%S')}** 到 **{target_end_time.strftime('%Y-%m-%d %H:%M:%S')}** (共 {round(total_duration_days, 2)} 天)")
    print(f"  采集间隔: **{current_interval} 秒**")
    print(f"  **预计总调用次数：约 129,600 次**")
    print(f"  **数据将输出到文件: {OUTPUT_FILENAME}**\n")
    
    # 1. 等待到精确的开始时间
    time_to_wait_for_start = (target_start_time - datetime.now()).total_seconds()
    
    if time_to_wait_for_start > 0:
        # 格式化打印等待时间
        wait_days = int(time_to_wait_for_start / 86400)
        wait_hours = int((time_to_wait_for_start % 86400) / 3600)
        wait_minutes = int((time_to_wait_for_start % 3600) / 60)
        
        print(f"--- ⏳ 等待 {wait_days} 天 {wait_hours} 小时 {wait_minutes} 分钟，直到 {target_start_time.strftime('%Y-%m-%d %H:%M:%S')} 开始采集... ---")
        time.sleep(time_to_wait_for_start)
    
    print("\n--- ✅ 到达开始时间，采集任务正式启动 ---")
    
    collection_count = 0
    next_target_time = target_start_time

    # 写入 CSV 文件头部
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        f.write("Timestamp,Road_Segment,Duration_Minutes,APICall_Status\n")
    
    # 2. 在时间窗口内进行循环采集
    while datetime.now() < target_end_time:
        
        # 确保在目标时间点启动采集
        wait_to_target = (next_target_time - datetime.now()).total_seconds()
        if wait_to_target > 0:
            time.sleep(wait_to_target)
            current_dt = next_target_time 
        else:
            if datetime.now() > next_target_time + timedelta(seconds=1): 
                 print(f"⚠️ 警告：采集点 {next_target_time.strftime('%Y-%m-%d %H:%M:%S')} 已错过，立即补采。")
            current_dt = datetime.now()
        
        timestamp_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        loop_start_time = time.time()
        
        collection_count += 1
        print(f"[{collection_count}] 正在采集... 记录时间: {timestamp_str}")
        
        # --- 调用 API ---
        travel_result, success = get_fastest_driving_time(ORIGIN_COORDINATE, DESTINATION_COORDINATE, MY_AMAP_KEY)
        
        api_status = "Success" if success else "Failure"
        
        # 准备日志记录的数据
        if success:
            log_duration = travel_result
            print(f"  -> 结果: **{log_duration} 分钟**")
        else:
            log_duration = travel_result # 失败时，log_duration 包含错误信息
            print(f"  -> 失败。返回信息: {log_duration}")

        # --- 记录日志 (CSV 格式) ---
        log_entry = f"{timestamp_str},{ROAD_SEGMENT_NAME},{log_duration},{api_status}\n"
        with open(OUTPUT_FILENAME, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
        print(f"  -> 记录已保存到 {OUTPUT_FILENAME}")

        # --- 更新下一个目标时间 ---
        next_target_time += timedelta(seconds=current_interval)
        
        # --- 检查是否已经超过最终结束时间 ---
        if next_target_time > target_end_time:
            print(f"--- 任务完成。下一个目标时间 ({next_target_time.strftime('%Y-%m-%d %H:%M:%S')}) 已超出结束时间。---")
            break
            
        # 打印等待信息（仅供显示）
        time_spent_on_call = time.time() - loop_start_time
        remaining_wait = (next_target_time - datetime.now()).total_seconds()
        
        if remaining_wait > 0:
             print(f"--- API耗时 {round(time_spent_on_call, 2)}s。等待 {round(remaining_wait, 2)} 秒。下一次采集预计在 {next_target_time.strftime('%Y-%m-%d %H:%M:%S')} ---")


    print("\n--- ✅ 采集任务结束 ---")
    print(f"  共采集 {collection_count} 次数据，所有数据都在 {OUTPUT_FILENAME} 文件中。")

if __name__ == "__main__":
    run_timed_collection()
