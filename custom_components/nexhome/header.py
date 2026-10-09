import hashlib
import time
import logging
import requests

_LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT = 10


class ServiceTool():
    def __init__(self, ip_address, sn):
        self.ip_address = ip_address
        self.sn = sn

    def get_ip_address(self):
        return self.ip_address

    def get_sn(self):
        return self.sn

    def getHeader(self):
        try:
            now_time = int(time.time() * 1000)
            now_time_md5 = hashlib.md5(str(now_time).encode()).hexdigest()

            if self.sn is None:
                return
            sn_md5 = hashlib.md5(self.sn.encode()).hexdigest()

            password_no_md5 = sn_md5.lower() + now_time_md5.lower()
            password = hashlib.md5(password_no_md5.encode()).hexdigest()
            return {
                "Time": str(now_time),
                "Password": password.lower(),
                "Appid": str(10000106),
                "Version": 'v1',
            }

        except Exception as exception:
            _LOGGER.error("SmartGatewayNativeAuthorizer error", exc_info=exception)


    def loginApi(self):
        try:
            Headers = self.getHeader()
            url = f"http://{self.ip_address}/smarthome/login"
            data = {
                'ip': '127.0.0.1'
            }
            return requests.post(url, headers=Headers, json=data, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            _LOGGER.error("请求失败: %s", e)
            return False
    # 登录
    async def login(self, hass):
        try:
            response = await hass.async_add_executor_job(self.loginApi)
            return response
        except requests.exceptions.RequestException as e:
            _LOGGER.error("请求失败: %s", e)
            return False

    # 获取场景列表
    def sceneList(self):
        Headers = self.getHeader()
        url = f"http://{self.ip_address}/smarthome/scenes"
        return requests.get(url, headers=Headers, timeout=REQUEST_TIMEOUT)

    # 获取设备属性
    def devicePost(self, params):
        Headers = self.getHeader()
        url = f"http://{self.ip_address}/smarthome/devices/properties/realtime"
        data = {
            'properties': params
        }
        return requests.post(url, headers=Headers, json=data, timeout=REQUEST_TIMEOUT)

    # 获取设备列表
    def deviceList(self):
        try:
            Headers = self.getHeader()
            url = f"http://{self.ip_address}/smarthome/devices"
            return requests.get(url, headers=Headers, timeout=REQUEST_TIMEOUT)
        except Exception as e:
            _LOGGER.error("请求失败: %s", e)
            return False  # 返回默认值

    # 设备控制
    def device_control(self, data, address):
        try:
            Headers = self.getHeader()
            return requests.post(
                f"http://{self.ip_address}/smarthome/devices/{address}/control",
                headers=Headers,
                json=data,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            _LOGGER.error("请求失败: %s", e)
            return False  # 返回默认值

    # 批量设备控制
    def batch_device_control(self, data):
        try:
            Headers = self.getHeader()
            params = {"devices": data}
            return requests.post(
                f"http://{self.ip_address}/smarthome/devices/control",
                headers=Headers,
                json=params,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            _LOGGER.error("请求失败: %s", e)
            return False  # 返回默认值

    async def getDevice(self, hass):
        try:
            response = await hass.async_add_executor_job(self.deviceList)
            if not response:
                return False
            response.raise_for_status()
            return response.json().get('result', {}).get('elements', [])
        except Exception as e:
            _LOGGER.error("获取设备列表失败: %s", e)
            return False  # 返回默认值

    async def getScene(self, hass):
        try:
            response = await hass.async_add_executor_job(self.sceneList)
            if not response:
                return False
            response.raise_for_status()
            return response.json().get('result', {}).get('elements', [])
        except Exception as e:
            _LOGGER.error("获取场景列表失败: %s", e)
            return False  # 返回默认值
    # 获取设备
    async def getProperties(self, hass, params):
        try:
            response = await hass.async_add_executor_job(self.devicePost, params)
            if not response:
                return False
            response.raise_for_status()  # 检查请求是否成功
            device_property = response.json().get('result', {}).get('deviceProperty')
            if device_property and len(device_property) > 0:
                return device_property
            else:
                return False
        except Exception as e:
            _LOGGER.error("获取设备属性失败: %s", e)
            return False  # 返回默认值
