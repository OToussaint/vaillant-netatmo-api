import sys
import os

# Add the project root to path to avoid token.py conflict
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Remove the current directory from path to force the use of the correct token module
current_dir = os.path.dirname(__file__)
if current_dir in sys.path:
    sys.path.remove(current_dir)

import asyncio
from vaillant_netatmo_api import auth_client, thermostat_client, Token

async def main():
    # For Vaillant Vsmart
    CLIENT_ID = "na_client_android_vaillant"
    CLIENT_SECRET = "XXXXXXXXXXXXXXXXXXXXXXX" # see https://community.home-assistant.io/t/added-support-for-vaillant-thermostat-how-to-integrate-in-official-release/31858
    USERNAME = "MY_VAILLANT_APP_USERNAME"
    PASSWORD = "MY_VAILLANT_APP_PWD"
    USER_PREFIX = "vaillant"
    APP_VERSION = "1.0.4.0"

    # For MiGo Vsmart
    # CLIENT_ID = "na_client_android_sdbg"
    # CLIENT_SECRET = "XXXXXXXXXXXXXXXXXXXXXXX" # see https://community.home-assistant.io/t/added-support-for-vaillant-thermostat-how-to-integrate-in-official-release/31858
    # USERNAME = "MY_MIGO_APP_USERNAME"
    # PASSWORD = "MY_MIGO_APP_PWD"
    # USER_PREFIX = "sdbg"
    # APP_VERSION = "1.3.0.4"
    
    if CLIENT_SECRET == "XXXXXXXXXXXXXXXXXXXXXXX":
        print("ERROR: You MUST replace CLIENT_SECRET, USERNAME and PASSWORD with your actual credentials!")
        return

    print("=== STEP 1: Getting token ===")
    
    token_container = [None]
    
    def handle_token_update(new_token):
        token_container[0] = new_token
        print(f"Token obtained")
    
    async with auth_client(CLIENT_ID, CLIENT_SECRET, handle_token_update) as auth:
        await auth.async_token(USERNAME, PASSWORD, USER_PREFIX, APP_VERSION)
    
    token = token_container[0]
    
    if token is None:
        print("ERROR: No token obtained!")
        return
    
    print("\n=== STEP 2: Testing async_get_home_data ===")
    
    async with thermostat_client(CLIENT_ID, CLIENT_SECRET, token, handle_token_update) as client:
        try:
            homes = await client.async_get_home_data()
            
            print(f"SUCCESS! Homes found: {len(homes)}")
            
            for home in homes:
                print(f"HOME_ID = '{home.home_id}'")
                if home.rooms:
                    print(f"ROOM_ID = '{home.rooms[0].room_id}'")
                if home.modules:
                    print(f"MODULE_ID = '{home.modules[0].module_id}'")
                    
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())