# 路径规划与天气数据采集工具

本项目用于定时采集高德地图的路径规划数据和天气数据。

## 📋 项目说明

包含两个数据采集脚本：
- **`time_record.py`**: 采集路径规划的实时行程时间
- **`weather_record.py`**: 采集城市的实时天气数据

## 🚀 快速开始

### 1. 安装依赖

```bash
uv sync
# 或者
pip install -r requirements.txt
```

### 2. 配置 API Key

编辑 `.env` 文件，填入您的高德地图 API Key：

```env
AMAP_KEY=your_amap_key_here
```

### 3. 运行脚本

#### 交通数据采集
```bash
python time_record.py
```

#### 天气数据采集
```bash
python weather_record.py
```

## ⚙️ 配置说明

### 基础配置（`.env` 文件）

```env
# 高德地图 API 配置（必需）
AMAP_KEY=your_amap_key_here

# 路径规划配置
ORIGIN_COORDINATE=113.8070,23.0450
DESTINATION_COORDINATE=114.0150,22.8550
ROAD_SEGMENT_NAME=石碣互通立交 - 塘厦立交

# 天气配置
DONGGUAN_CITY_NAME=东莞

# 采集间隔配置
TIME_COLLECTION_INTERVAL_SECONDS=20      # 交通数据采集间隔（秒）
WEATHER_COLLECTION_INTERVAL_MINUTES=10   # 天气数据采集间隔（分钟）
```

### 可选：时间窗口配置

如果需要在特定时间范围内采集数据，可以取消注释并配置时间窗口：

```env
# 交通数据时间窗口（可选）
TIME_START_YEAR=2026
TIME_START_MONTH=1
TIME_START_DAY=1
TIME_START_HOUR=23
TIME_START_MINUTE=59
TIME_START_SECOND=0

TIME_END_YEAR=2026
TIME_END_MONTH=2
TIME_END_DAY=1
TIME_END_HOUR=0
TIME_END_MINUTE=0
TIME_END_SECOND=0

# 天气数据时间窗口（可选）
WEATHER_START_YEAR=2026
WEATHER_START_MONTH=1
WEATHER_START_DAY=3
WEATHER_START_HOUR=23
WEATHER_START_MINUTE=20
WEATHER_START_SECOND=0

WEATHER_END_YEAR=2026
WEATHER_END_MONTH=1
WEATHER_END_DAY=31
WEATHER_END_HOUR=23
WEATHER_END_MINUTE=59
WEATHER_END_SECOND=0
```

**注意**：
- 如果不配置时间窗口，脚本将直接启动并持续运行
- 如果配置了时间窗口，脚本会在窗口内持续采集
- 时间窗口配置为可选，未配置时使用默认值 0，会被识别为无时间窗口限制

## 📊 数据输出

### 文件位置
所有数据保存在 `data/` 目录下

### 文件命名格式
- 交通数据：`traffic_data_YYYYMMDD_HHMMSS.csv`
- 天气数据：`weather_data_YYYYMMDD_HHMMSS.csv`

### CSV 格式

**交通数据** (`time_record.py`):
```csv
Timestamp,Road_Segment,Duration_Minutes,APICall_Status
2026-01-05 12:00:00,石碣互通立交 - 塘厦立交,45.5,Success
2026-01-05 12:00:20,石碣互通立交 - 塘厦立交,46.2,Success
```

**天气数据** (`weather_record.py`):
```csv
Timestamp,Weather,Temp_C,Wind_Dir,Wind_Power,Status
2026-01-05 12:00:00,晴,22,北风,2级,Success
2026-01-05 12:10:00,多云,23,东北风,1级,Success
```

## 🔧 功能特点

### 本次修订内容（2026-01-05）

#### ✅ 修复的问题：
1. **配置安全性**：API Key 从代码中移除，改用 `.env` 文件管理
2. **数据追加**：修复了之前会删除旧文件的问题，现在正确追加数据
3. **启动逻辑**：删除了启动时间等待，脚本直接从当前时间开始运行
4. **补录逻辑**：移除了错误的补录机制，错过时间点直接使用当前时间
5. **数据组织**：数据统一保存到 `data/` 目录，文件名包含时间戳避免覆盖

#### 📁 文件结构：
```
zy_route_record/
├── .env                    # 配置文件（需自行填写 API Key）
├── requirements.txt        # Python 依赖
├── time_record.py          # 交通数据采集脚本
├── weather_record.py       # 天气数据采集脚本
├── data/                   # 数据输出目录（自动生成）
│   ├── traffic_data_*.csv
│   └── weather_data_*.csv
└── README.md              # 本说明文档
```

## ⚠️ 注意事项

1. **API 限制**：高德地图 API 有调用频率限制，请合理设置采集间隔
2. **网络异常**：脚本会自动处理网络异常，失败记录会保存到 CSV 中
3. **中断恢复**：脚本支持 `Ctrl+C` 中断，数据会实时保存不会丢失
4. **文件权限**：确保有权限在当前目录创建 `data/` 文件夹和写入文件

## 📞 故障排查

### API Key 错误
- 检查 `.env` 文件中的 `AMAP_KEY` 是否正确
- 确认 API Key 是否有调用权限

### 数据未保存
- 检查是否有 `data/` 目录的写入权限
- 查看脚本输出的错误信息

### 采集间隔异常
- 如果 API 耗时超过采集间隔，会显示警告并立即开始下一轮采集
- 可适当增加采集间隔以避免此问题
