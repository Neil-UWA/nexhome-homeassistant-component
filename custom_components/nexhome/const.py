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

# 轮询时间（秒）
TIME_NUMBER = 3

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
