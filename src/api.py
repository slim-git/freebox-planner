import time
import threading
from datetime import datetime, timedelta
from fastapi import FastAPI
from src.main import Fbxpy
from src.main import log_info, log_error, log_exception
from src.main import WifiState, WifiPlanningState
from contextlib import asynccontextmanager

# ===============================================================
# FastAPI app
# ===============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the thread to check WiFi state
    log_info("Starting WiFi check thread...")
    
    # Create a thread to run the wifi_check_loop function
    # Set it as a daemon thread so it will not block the program
    # from exiting when the main thread ends
    thread = threading.Thread(target=wifi_check_loop, daemon=True)
    thread.start()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def health_check():
    return {"status": "✅ App is running"}

@app.get("/wifi")
def wifi_check():
    return enable_wifi()

def wifi_check_loop():
    while True:
        try:
            # Get current datetime
            current_time = datetime.now()
            
            log_info(current_time.strftime("%d/%m/%Y, %H:%M:%S"))
            
            # Check if minute is 29 or 59
            if 29 == current_time.minute % 30:
                enable_wifi()
        
        except Exception as e:
            log_exception(f"An error occurred: {e}")
        
        finally:
            # Compute the number of seconds from now to the next_run_time date
            current_time = datetime.now().replace(microsecond=0)
            
            if current_time.minute < 29:
                next_run_time = current_time.replace(minute=29, second=0)
            elif current_time.minute < 59:
                next_run_time = current_time.replace(minute=59, second=0)
            else:
                next_run_time = current_time.replace(minute=59, second=0) + timedelta(minutes=30)
            
            seconds_until = (next_run_time - current_time).total_seconds()
            
            # Sleep for that duration
            log_info(f"Sleeping for {seconds_until} seconds until {next_run_time.strftime("%H:%M:%S")}.")
            time.sleep(seconds_until)

def enable_wifi():
    """
    Check the WiFi state and planning state.
    If the WiFi is inactive, activate it.
    If the WiFi planning is active, disable it.
    """
    fbxpy = Fbxpy()
    log_info("Checking WiFi state...")
    wifi_state = fbxpy.get_wifi_state()

    # Activate the wifi if needed
    if wifi_state == WifiState.INACTIVE:
        log_info("WiFi is inactive, trying to activate...")
        if fbxpy.activate_wifi():
            log_info("WiFi activated successfully.")
        else:
            log_error("Failed to activate WiFi.")
    
    # Check the planning state and disable it if needed
    if fbxpy.get_wifi_planning_state() == WifiPlanningState.TRUE:
        log_info("WiFi planning is active, trying to disable...")
        
        if fbxpy.set_wifi_planning_state(False):
            log_info("WiFi planning disabled successfully.")
        else:
            log_error("Failed to disable WiFi planning.")
    
    return {
        "wifi_state": wifi_state,
        "wifi_planning_state": fbxpy.get_wifi_planning_state()
    }