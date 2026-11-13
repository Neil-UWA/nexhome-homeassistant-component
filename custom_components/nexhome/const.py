from homeassistant.const import Platform


IP = '192.168.10.1:8085'
DEVICES = "devices"
SCENES = "scene"
DOMAIN = "nexhome"
SN_CONFIG = 'sn_input'
IP_CONFIG = "ip_address"
DEVICE_DATA = "device_list"
DISCOVER = 'discover_obj'
FILTER_MODE_CONFIG = "filter_mode"  # "include" 或 "exclude"
FILTER_DEVICES_CONFIG = "filter_devices"  # 设备ID列表

# 推送更新信号前缀（每个设备一个信号: {SIGNAL_PUSH_UPDATE}_{device_address}）
SIGNAL_PUSH_UPDATE = f"{DOMAIN}_push_update"
# UDP 推送监听器在 hass.data 中的键
UDP_LISTENER = "udp_listener"
# 推送模式是否启用
PUSH_ENABLED = "push_enabled"
# 控制命令专用线程池
CONTROL_EXECUTOR = "control_executor"
# 轮询请求专用线程池
POLL_EXECUTOR = "poll_executor"
# 网关请求调度器（控制优先、轮询串行错峰）
GATEWAY_SCHEDULER = "gateway_scheduler"
# 控制请求进行中及完成后暂停轮询的时长（秒）
CONTROL_POLL_PAUSE_SECONDS = 2.0
# 相邻两次轮询请求之间的最小间隔（秒）
POLL_MIN_GAP_SECONDS = 0.2
# 合并轮询时单次 realtime 请求最多包含的属性项数（实测 380 项约 0.35s）
POLL_BATCH_SIZE = 400
# 场景列表刷新间隔（秒），场景很少变化，无需高频拉取
SCENE_POLL_INTERVAL = 60

# 轮询时间（秒）：有活动时的基础轮询间隔
TIME_NUMBER = 3

# ---- 自适应轮询（选项中可配置） ----
OPT_POLL_INTERVAL = "poll_interval"            # 活跃时轮询间隔（秒）
OPT_IDLE_MAX_INTERVAL = "idle_max_interval"    # 空闲时轮询间隔上限（秒）
OPT_QUIET_ENABLED = "quiet_enabled"            # 是否启用静默时段（如夜间）
OPT_QUIET_START = "quiet_start"                # 静默时段开始（HH:MM:SS）
OPT_QUIET_END = "quiet_end"                    # 静默时段结束（HH:MM:SS）
OPT_QUIET_INTERVAL = "quiet_interval"          # 静默时段空闲轮询间隔（秒），0 = 停止轮询仅靠推送
DEFAULT_IDLE_MAX_INTERVAL = 30
DEFAULT_QUIET_ENABLED = False
DEFAULT_QUIET_START = "23:00:00"
DEFAULT_QUIET_END = "07:00:00"
DEFAULT_QUIET_INTERVAL = 300
# 最近一次活动（状态变化/推送/控制）后保持基础间隔的时长（秒），之后开始逐步拉长
ACTIVE_WINDOW_SECONDS = 60
# 静默时段停止轮询时，协调器检查是否需要恢复的间隔（秒，不发请求）
PAUSED_CHECK_SECONDS = 60
# 持续波动的测量值，不作为“有人操作”的活动信号
SENSOR_IDENTIFIERS = {
    "Temperature", "Humidity", "PM25", "PM10", "HCHO", "CO2", "LUX", "VOC",
}

FAN_MODEL_MAP = {
    "0": "自动",
    "1": "低速",
    "2": "中速",
    "3": "高速",
    "4": "超静",
    "5": "超强",
    "6": "中低",
    "7": "中高",
}

EXTRA_SENSOR = [Platform.SENSOR]
EXTRA_SWITCH = [Platform.SWITCH, Platform.NUMBER, Platform.SELECT, Platform.COVER]
EXTRA_CONTROL = [Platform.CLIMATE, Platform.FAN, Platform.LIGHT]
ALL_PLATFORM =  EXTRA_SENSOR + EXTRA_CONTROL + EXTRA_SWITCH

PowerSwitch = "PowerSwitch"
TemperatureSet = "TemperatureSet"
Temperature = "Temperature"
Windspeed = "Windspeed"
WorkMode = "WorkMode"
WindDirection = "WindDirection"
Location = "Location"
Brightness = "Brightness"
Humidity = "Humidity"
ColorTem = "ColorTem"
Close = "Close"
Open = "Open"
Stop = "Stop"
PM25 = "PM25"
PM10 = "PM10"
HCHO = "HCHO"
CO2 = "CO2"
LUX = "LUX"
VOC = "VOC"
Default_Device = {
    'id': 'teshudechangjingmianban',
    'address': '680AE2FFFE33326D-2222222',
    'name': '场景面板',
    'type': 'default',
}
