import os
import datetime
import hashlib
import hmac
import json
import time
import requests
import urllib3
from threading import Thread, Lock
from typing import Optional, Dict
from requests import Session
from dotenv import load_dotenv
from src.enums import (
    Endpoint,
    WifiState,
    WifiPlanningState
)
from src.logs import (
    log_debug,
    log_info,
    log_exception,
    log_error,
)

load_dotenv()

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
        """
        Get the singleton instance of Fbxpy.
        """
        if cls._instance is None:
            cls._instance = Fbxpy()
        return cls._instance
    
    def update_last_use(self):
        """
        Update the last use time of the session.
        """
        self.last_use = time.time()

    def get_session(self) -> Session:
        """
        Get the current session, creating it if necessary.
        """
        if self.current_session is None:
            self.create_session()
        return self.current_session

    def check_time(self):
        """
        Check if the session is still valid and close it if not.
        """
        can_continue = True
        
        while can_continue:
            time.sleep(10)
            if self.current_session is None:
                can_continue = False
            elif (time.time() - self.last_use) >= 60:
                can_continue = False
                self.close_session()
                log_info("Session closed due to inactivity.")

    def connexion_post(self,
                       method: Endpoint,
                       data: Optional[Dict] = None):
        """
        Send a POST request to the server.
        """
        url = URL_BASE + method.value
        if data:
            data = json.dumps(data)
        with self.lock:
            result = json.loads(self.get_session().post(url, data=data).text)
            self.update_last_use()
        return result

    def connexion_post_without_connection(self,
                                          method: Endpoint,
                                          data: Optional[Dict] = None,
                                          session: Session = None):
        """
        Send a POST request to the server without using the current session.
        """
        url = URL_BASE + method.value
        if data:
            data = json.dumps(data)
        return json.loads(session.post(url, data=data).text)

    def connexion_get(self, method: Endpoint):
        """
        Send a GET request to the server.
        """
        url = URL_BASE + method.value
        with self.lock:
            result = json.loads(self.get_session().get(url).text)
            self.update_last_use()
        return result

    def connexion_get_without_connection(self,
                                         method: Endpoint,
                                         session: Session):
        """
        Send a GET request to the server without using the current session.
        """
        url = URL_BASE + method.value
        return json.loads(session.get(url).text)

    def connexion_put(self,
                      method: Endpoint,
                      data: Optional[Dict] = None):
        """
        Send a PUT request to the server.
        """
        url = URL_BASE + method.value
        if data:
            data = json.dumps(data)
        with self.lock:
            log_info(url)
            log_info(data)
            result = json.loads(self.get_session().put(url, data=data).text)
            self.update_last_use()
        return result

    def create_session(self) -> Session:
        """
        Create a new session with the server.
        """
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
        log_debug(content)
        session.headers = {"X-Fbx-App-Auth": content["result"]["session_token"]}
        self.current_session = session
        self.update_last_use()
        Thread(None, self.check_time, 'check_time_thread', (), {}).start()
        
        return session

    def close_session(self):
        """
        Close the current session.
        """
        if self.current_session is None:
            return
        
        try:
            self.connexion_post(Endpoint.LOGIN_LOGOUT)
        except Exception as e:
            log_exception(e)
        finally:
            self.current_session = None

    def get_wifi_state(self) -> WifiState:
        """
        Get the current state of the WiFi.
        """
        try:
            result = self.connexion_get(method=Endpoint.WIFI_AP)
            
            # Loop over the access points
            for ap in result["result"]:
                state = WifiState.get_by_value(ap["status"]["state"])
            
                if state == WifiState.ACTIVE:
                    if self.get_wifi_planning_state() == WifiPlanningState.TRUE:
                        return WifiState.ACTIVE_PLANIF
                    else:
                        return WifiState.ACTIVE
                elif state in [WifiState.INACTIVE, WifiState.DISABLED]:
                    return WifiState.INACTIVE
        
        except Exception as e:
            log_exception(e)
        
        return WifiState.UNKNOWN

    def get_wifi_planning_state(self) -> WifiPlanningState:
        """
        Get the current state of the WiFi planning.
        """
        try:
            result = self.connexion_get(method=Endpoint.WIFI_PLANNING)
            
            if result["result"]["use_planning"]:
                return WifiPlanningState.TRUE
            else:
                return WifiPlanningState.FALSE
        except Exception as e:
            log_exception(e)
        
        return WifiPlanningState.UNKNOWN

    def set_wifi_planning_state(self, value: bool) -> bool:
        """
        Set the state of the WiFi planning.
        """
        try:
            result = self.connexion_put(Endpoint.WIFI_PLANNING,
                                        data={"use_planning": value})
            
            if result["success"] and result["result"]["use_planning"]:
                return True
        
        except Exception as e:
            log_exception(e)
        
        return False

    def activate_wifi(self) -> bool:
        """
        Activate the WiFi.
        """
        result = self.connexion_put(method=Endpoint.WIFI_CONFIG,
                                    data={"enabled": True})
        
        if result["success"]:
            return True
        else:
            return False

    def stop_wifi(self) -> bool:
        """
        Stop the WiFi.
        """
        try:
            result = self.connexion_put(method=Endpoint.WIFI_CONFIG,
                                        data={"enabled": False})
            
            if result["success"] and not result["result"]["enabled"]:
                return True
        
        except Exception as e:
            log_exception(e)
        
        return False

singleton = Fbxpy.get_instance()

# =====================================================================
if __name__ == "__main__":
    # Keep wifi up
    while True:
        try:
            # Get current datetime
            current_time = datetime.datetime.now()
            
            log_info(current_time.strftime("%d/%m/%Y, %H:%M:%S"))
            
            # Check if minute is 29 or 59
            if 29 == current_time.minute % 30:
                log_info("Checking WiFi state...")
                wifi_state = singleton.get_wifi_state()

                # Activate the wifi if needed
                if wifi_state == WifiState.INACTIVE:
                    log_info("WiFi is inactive, trying to activate...")
                    if singleton.activate_wifi():
                        log_info("WiFi activated successfully.")
                    else:
                        log_error("Failed to activate WiFi.")
                
                # Check the planning state and disable it if needed
                if singleton.get_wifi_planning_state() == WifiPlanningState.TRUE:
                    log_info("WiFi planning is active, trying to disable...")
                    
                    if singleton.set_wifi_planning_state(False):
                        log_info("WiFi planning disabled successfully.")
                    else:
                        log_error("Failed to disable WiFi planning.")
        
        except Exception as e:
            log_exception(f"An error occurred: {e}")
        
        finally:
            # Compute the number of seconds from now to the next_run_time date
            current_time = datetime.datetime.now().replace(microsecond=0)
            
            if current_time.minute < 29:
                next_run_time = current_time.replace(minute=29, second=0)
            else:
                next_run_time = current_time.replace(minute=59, second=0)
            
            seconds_until = (next_run_time - current_time).total_seconds()
            
            # Sleep for that duration
            log_info(f"Sleeping for {seconds_until} seconds until {next_run_time.strftime("%H:%M:%S")}.")
            time.sleep(seconds_until)
            