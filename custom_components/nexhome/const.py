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

# 轮询时间（秒）
TIME_NUMBER = 3
# 推送模式下的回退轮询时间（秒）
TIME_NUMBER_PUSH_FALLBACK = 60

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
