import os
import requests
from dotenv import load_dotenv
from src.enums import Endpoint
from src.logs import log_info

load_dotenv()

# Load environment variables from .env file
URL_BASE = os.getenv('URL_BASE')
APP_ID = os.getenv('APP_ID')
APP_NAME = os.getenv('APP_NAME')
APP_VERSION = os.getenv('APP_VERSION')
DEVICE_NAME = os.getenv('DEVICE_NAME')

def register_app():
    """
    Register the application with the server.
    """

    response = requests.post(
        URL_BASE + Endpoint.LOGIN_AUTHORIZE.value,
        json={
            'app_id': APP_ID,
            'app_name': APP_NAME,
            'app_version': APP_VERSION,
            'device_name': DEVICE_NAME
        },
        verify=False
    )
    response.raise_for_status()
    content = response.json()

    log_info(content)

    token = str(content["result"]["app_token"])
    track_id = str(content["result"]["track_id"])

    return {
        "token": token,
        "track_id": track_id
    }

def confirm_registration(app_token: str, track_id: str) -> bool:
    """
    Confirm the registration of the application with the server.
    This function will be called when the user authorizes the application on the Freebox server.
    It will check the status of the registration process and return True if the registration is successful.
    If the registration is refused, it will return False.
    If there is an error during the registration process, it will return False.

    :param app_token: The application token received during registration.
    :param track_id: The track ID received during registration.
    :return: True if the registration is successful, False otherwise.
    """
    try:
        response = requests.get(
            URL_BASE + Endpoint.LOGIN_AUTHORIZE.value + track_id,
            headers={
                'X-Fbx-App-Auth': app_token
            },
            verify=False
        )
        response.raise_for_status()
        content = response.json()

        if content["result"] != "success" or content["result"]["status"] == "denied":
            log_info("Registration refused.")
            return False
        
        return True
    except Exception as e:
        log_info(f"Error during registration confirmation: {e}")
        return False

# ===============================================================
if __name__ == "__main__":
    registration_data = register_app()
    
    # Wait until user authorizes the app on the Freebox server
    input("Go to your Freebox server to authorize the app (and hurry up, you only have a few seconds to do so!).\nPress any key when done...")
    
    # Check the progress of the registration process
    result = confirm_registration(registration_data["token"], registration_data["track_id"])
    if result:
        log_info("Registration complete! Save the token and track_id in your .env file for future use.")
        print(f"token: {registration_data['token']}\ntrack_id: {registration_data['track_id']}")
    else:
        log_info("Registration confirmation failed.")
