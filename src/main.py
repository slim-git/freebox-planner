import os
import datetime
import hashlib
import hmac
import json
import time
import requests
import urllib3
import logging
from threading import Thread, Lock
from typing import Optional, Dict
from requests import Session
from dotenv import load_dotenv
from src.enums import Endpoint, WifiState, WifiPlanningState

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
URL_BASE = os.getenv('URL_BASE')
APP_ID = os.getenv('APP_ID')
APP_NAME = os.getenv('APP_NAME')
APP_VERSION = os.getenv('APP_VERSION')
DEVICE_NAME = os.getenv('DEVICE_NAME')

TOKEN = os.getenv('TOKEN')
TRACK_ID = os.getenv('TRACK_ID')

urllib3.disable_warnings()

class Fbxpy():
    _instance: 'Fbxpy' = None

    lock: Lock
    current_session: Session
    last_use: int

    def __init__(self):
        super().__init__()
        self.lock = Lock()
        self.current_session = None
        self.last_use = 0

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Fbxpy()
        return cls._instance
    
    @classmethod
    def fancy_print(cls, data):
        logger.info(json.dumps(data, indent=2, separators=(',', ': ')))
    
    def update_last_use(self):
        self.last_use = time.time()

    def get_session(self) -> Session:
        if self.current_session is None:
            self.create_session()
        return self.current_session

    def check_time(self):
        can_continue = True
        
        while can_continue:
            time.sleep(10)
            if self.current_session is None:
                can_continue = False
            elif (time.time() - self.last_use) >= 60:
                can_continue = False
                self.close_session()
                logger.info("Session closed due to inactivity.")

    def connexion_post(self, method: Endpoint, data: Optional[Dict] = None):
        url = URL_BASE + method.value
        if data:
            data = json.dumps(data)
        with self.lock:
            result = json.loads(self.get_session().post(url, data=data).text)
            self.update_last_use()
        return result

    def connexion_post_without_connection(self, method: Endpoint, data: Optional[Dict] = None, session: Session = None):
        url = URL_BASE + method.value
        if data:
            data = json.dumps(data)
        return json.loads(session.post(url, data=data).text)

    def connexion_get(self, method: Endpoint):
        url = URL_BASE + method.value
        with self.lock:
            result = json.loads(self.get_session().get(url).text)
            self.update_last_use()
        return result

    def connexion_get_without_connection(self, method: Endpoint, session: Session):
        url = URL_BASE + method.value
        return json.loads(session.get(url).text)

    def connexion_put(self, method: Endpoint, data: Optional[Dict] = None):
        url = URL_BASE + method.value
        if data:
            data = json.dumps(data)
        with self.lock:
            self.fancy_print(url)
            self.fancy_print(data)
            result = json.loads(self.get_session().put(url, data=data).text)
            self.update_last_use()
        return result

    def register(self):
        global TOKEN, TRACK_ID
        payload = {
            'app_id': APP_ID,
            'app_name': APP_NAME,
            'app_version': APP_VERSION,
            'device_name': DEVICE_NAME
        }
        content = self.connexion_post(Endpoint.LOGIN_AUTHORIZE, payload)
        self.fancy_print(content)
        TOKEN = str(content["result"]["app_token"])
        TRACK_ID = str(content["result"]["track_id"])

    def progress(self):
        content = self.connexion_get(Endpoint.LOGIN_AUTHORIZE + TRACK_ID)
        self.fancy_print(content)

    def create_session(self) -> Session:
        session = requests.session()
        session.verify = False
        challenge = str(self.connexion_get_without_connection(Endpoint.LOGIN, session)["result"]["challenge"])
        token_bytes = bytes(TOKEN, 'latin-1')
        challenge_bytes = bytes(challenge, 'latin-1')
        password = hmac.new(token_bytes, challenge_bytes, hashlib.sha1).hexdigest()
        data = {
            "app_id": APP_ID,
            "app_version": APP_VERSION,
            "password": password
        }
        content = self.connexion_post_without_connection(Endpoint.LOGIN_SESSION, data, session)
        session.headers = {"X-Fbx-App-Auth": content["result"]["session_token"]}
        self.current_session = session
        self.update_last_use()
        Thread(None, self.check_time, 'check_time_thread', (), {}).start()
        
        return session

    def close_session(self):
        self.connexion_post(Endpoint.LOGIN_LOGOUT)
        self.current_session = None

    def get_wifi_state(self) -> WifiState:
        try:
            result = self.connexion_get(method=Endpoint.WIFI_AP)
            
            state = WifiState.get_by_value(result["result"][0]["status"]["state"])
            
            if state == WifiState.ACTIVE:
                if self.get_wifi_planning_state() == WifiPlanningState.TRUE:
                    return WifiState.ACTIVE_PLANIF
                else:
                    return WifiState.ACTIVE
        
        except Exception as e:
            logger.error(e)
        
        return WifiState.UNKNOWN

    def get_wifi_planning_state(self) -> WifiPlanningState:
        try:
            result = self.connexion_get(method=Endpoint.WIFI_PLANNING)
            
            if result["result"]["use_planning"]:
                return WifiPlanningState.TRUE
            else:
                return WifiPlanningState.FALSE
        except Exception as e:
            logger.error(e)
        
        return WifiPlanningState.UNKNOWN

    def set_wifi_planning_state(self, value: bool) -> bool:
        try:
            result = self.connexion_put(Endpoint.WIFI_PLANNING,
                                        data={"use_planning": value})
            
            if result["success"] and result["result"]["use_planning"]:
                return True
        
        except Exception as e:
            logger.error(e)
        
        return False

    def active_wifi(self) -> bool:
        result = self.connexion_put(method=Endpoint.WIFI_CONFIG,
                                    data={"enabled": True})
        
        if result["success"]:
            return True
        else:
            return False

    def stop_wifi(self) -> bool:
        try:
            result = self.connexion_put(method=Endpoint.WIFI_CONFIG,
                                        data={"enabled": False})
            
            if result["success"] and not result["result"]["enabled"]:
                return True
        
        except Exception as e:
            logger.error(e)
        
        return False

singleton = Fbxpy.get_instance()

if __name__ == "__main__":
    while True:
        try:
            logger.info("Checking WiFi state...")
            # Get current datetime
            current_time = datetime.datetime.now()
            
            # Check if minute is 29 or 59
            if 29 == current_time.minute % 30:
                logger.info("Current minute is 29 or 59, checking WiFi state...")
                wifi_state = singleton.get_wifi_state()

                # Activate the wifi if needed
                if wifi_state == WifiState.INACTIVE:
                    logger.info("WiFi is inactive, trying to activate...")
                    if singleton.active_wifi():
                        logger.info("WiFi activated successfully.")
                    else:
                        logger.error("Failed to activate WiFi.")
                
                # Check the planning state and disable it if needed
                if singleton.get_wifi_planning_state() == WifiPlanningState.TRUE:
                    logger.info("WiFi planning is active, trying to disable...")
                    
                    if singleton.set_wifi_planning_state(False):
                        logger.info("WiFi planning disabled successfully.")
                    else:
                        logger.error("Failed to disable WiFi planning.")
        
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        
        finally:
            # Sleep for a minute before checking again
            time.sleep(60)
            singleton.create_session()
            