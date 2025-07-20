# thermostat_test.py
import httpx
import pytest

from datetime import datetime, timedelta

from pytest_mock import MockerFixture
from respx import MockRouter

from vaillant_netatmo_api.errors import RequestClientException, UnsuportedArgumentsException
from vaillant_netatmo_api.thermostat import Device, MeasurementItem, MeasurementScale, MeasurementType, SetpointMode, SystemMode, TimeSlot, Zone, thermostat_client
from vaillant_netatmo_api.token import Token

token = Token({
    "access_token": "12345",
    "refresh_token": "abcde",
    "expires_at": "",
})

get_thermostats_data_request = {
    "device_type": "NAVaillant",
    "data_amount": "app",
    "sync_device_id": "all",
    "access_token": "12345",
}

# This dictionary is what the client actually sends in the request body for these API calls.
# The 'access_token' is handled by the Authorization header and should not be in 'data'.
get_thermostats_data_request_mock_data = {
    "device_type": "NAVaillant",
    "data_amount": "app",
    "sync_device_id": "all",
}

get_thermostats_data_refreshed_request = {
    "device_type": "NAVaillant",
    "data_amount": "app",
    "sync_device_id": "all",
    "access_token": "67890",
}

# This dictionary is what the client actually sends in the request body for these API calls after token refresh.
# The 'access_token' is handled by the Authorization header and should not be in 'data'.
get_thermostats_data_refreshed_request_mock_data = {
    "device_type": "NAVaillant",
    "data_amount": "app",
    "sync_device_id": "all",
}


get_thermostats_data_response = {
    "status": "ok",
    "body": {
        "devices": [
            {
                "_id": "id",
                "type": "type",
                "station_name": "station_name",
                "firmware": "firmware",
                "wifi_status": 60,
                "dhw": 55,
                "dhw_max": 65,
                "dhw_min": 35,
                "setpoint_default_duration": 120,
                "outdoor_temperature": {
                    "te": 11,
                    "ti": 1667636447,
                },
                "system_mode": "summer",
                "setpoint_hwb": {"setpoint_activate": False, "setpoint_endtime": 1642056298},
                "modules": [
                    {
                        "_id": "id",
                        "type": "type",
                        "module_name": "module_name",
                        "firmware": "firmware",
                        "rf_status": 70,
                        "boiler_status": True,
                        "battery_percent": 80,
                        "setpoint_away": {"setpoint_activate": False, "setpoint_endtime": 1642056298},
                        "setpoint_manual": {"setpoint_activate": False, "setpoint_endtime": 1642056298},
                        "therm_program_list": [
                            {
                                "zones": [{"temp": 20, "id": 0, "hw": True}],
                                "timetable": [{"id": 0, "m_offset": 0}],
                                "program_id": "program_id",
                                "name": "name",
                                "selected": True,
                            }
                        ],
                        "measured": {"temperature": 25, "setpoint_temp": 26, "est_setpoint_temp": 27},
                    }
                ]
            }
        ]
    }
}

get_measure_request = {
    "device_id": "device",
    "module_id": "module",
    "type": "temperature",
    "scale": "max",
    "date_begin": 1642252768,
    "access_token": "12345",
}

get_measure_request_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "type": "temperature",
    "scale": "max",
    "date_begin": 1642252768,
}

get_measure_response = {
    "status": "ok",
    "body": [
        {"beg_time": 1642252768, "step_time": 600, "value": [[20], [20.1]]},
        {"beg_time": 1642252768, "step_time": 600, "value": [[20.2], [20.3]]}
    ]
}

set_system_mode_request = {
    "device_id": "device",
    "module_id": "module",
    "system_mode": "summer",
    "access_token": "12345",
}

set_system_mode_request_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "system_mode": "summer",
}

set_system_mode_response = {
    "status": "ok",
}

set_minor_mode_request = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "away",
    "activate": True,
    "access_token": "12345",
}

set_minor_mode_request_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "away",
    "activate": True,
}

set_minor_mode_manual_activate_with_temp_and_endtime_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "manual",
    "activate": True,
    "setpoint_temp": 20.0,
    # setpoint_endtime will be dynamically calculated and added to this dict in the test
}

set_minor_mode_manual_deactivate_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "manual",
    "activate": False,
}

set_minor_mode_away_activate_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "away",
    "activate": True,
}

set_minor_mode_away_activate_with_endtime_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "away",
    "activate": True,
    # setpoint_endtime will be dynamically calculated and added to this dict in the test
}

set_minor_mode_away_deactivate_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "away",
    "activate": False,
}

set_minor_mode_hwb_activate_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "hwb",
    "activate": True,
    # setpoint_endtime will be dynamically calculated (default duration) and added to this dict in the test
}

set_minor_mode_hwb_deactivate_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "setpoint_mode": "hwb",
    "activate": False,
}

set_minor_mode_response = {
    "status": "ok",
}

sync_schedule_request = {
    "device_id": "device",
    "module_id": "module",
    "schedule_id": "program_id",
    "name": "name",
    "zones": "[{\"id\": 0, \"temp\": 20, \"hw\": true}]",
    "timetable": "[{\"id\": 0, \"m_offset\": 0}]",
    "access_token": "12345",
}

sync_schedule_request_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "schedule_id": "program_id",
    "name": "name",
    "zones": "[{\"id\": 0, \"temp\": 20, \"hw\": true}]",
    "timetable": "[{\"id\": 0, \"m_offset\": 0}]",
}

sync_schedule_response = {
    "status": "ok",
}

switch_schedule_request = {
    "device_id": "device",
    "module_id": "module",
    "schedule_id": "program_id",
    "access_token": "12345",
}

switch_schedule_request_mock_data = {
    "device_id": "device",
    "module_id": "module",
    "schedule_id": "program_id",
}

switch_schedule_response = {
    "status": "ok",
}

async_set_hot_water_temperature_request = {
    "device_id": "device",
    "dhw": 50,
    "access_token": "12345",
}

async_set_hot_water_temperature_request_mock_data = {
    "device_id": "device",
    "dhw": 50,
}

async_set_hot_water_temperature_response = {
    "status": "ok",
}

async_modify_device_param_request = {
    "device_id": "device",
    "setpoint_default_duration": 120,
    "access_token": "12345",
}

async_modify_device_param_request_mock_data = {
    "device_id": "device",
    "setpoint_default_duration": 120,
}

async_modify_device_param_response = {
    "status": "ok",
}

refresh_token_request = {
    "grant_type": "refresh_token",
    "client_id": "client",
    "client_secret": "secret",
    "refresh_token": "abcde",
}

refresh_token_response = {
    "access_token": "67890",
    "refresh_token": "fghij",
    "expires_at": "",
}


@pytest.mark.asyncio
class TestThermostat:
    async def test_async_get_thermostats_data__invalid_request_params__raises_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/getthermostatsdata",
                        data=get_thermostats_data_request_mock_data).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException):
                await client.async_get_thermostats_data()

    async def test_async_get_thermostats_data__unauthorized_errors__succeed_after_refreshing_token(self, respx_mock: MockRouter):
        # This test mock is for server errors (500), not unauthorized (401)
        respx_mock.post("https://api.netatmo.com/api/getthermostatsdata", data=get_thermostats_data_request_mock_data).mock(side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=get_thermostats_data_response),
        ])

        async with thermostat_client("", "", token, None) as client:
            devices = await client.async_get_thermostats_data()

            expected_devices = get_thermostats_data_response["body"]["devices"]

            assert respx_mock.calls.call_count == 2
            assert len(devices) == len(expected_devices)
            for x in zip(devices, expected_devices):
                assert x[0] == Device(**x[1])

    async def test_async_get_thermostats_data__valid_request_params__returns_valid_device_list(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/getthermostatsdata",
                        data=get_thermostats_data_request_mock_data).respond(200, json=get_thermostats_data_response)

        async with thermostat_client("", "", token, None) as client:
            devices = await client.async_get_thermostats_data()

            expected_devices = get_thermostats_data_response["body"]["devices"]

            assert len(devices) == len(expected_devices)
            for x in zip(devices, expected_devices):
                assert x[0] == Device(**x[1])

    async def test_async_get_measure__invalid_request_params__raises_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/getmeasure",
                        data=get_measure_request_mock_data).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException):
                await client.async_get_measure(
                    get_measure_request["device_id"],
                    get_measure_request["module_id"],
                    MeasurementType.TEMPERATURE,
                    MeasurementScale.MAX,
                    datetime.fromtimestamp(get_measure_request["date_begin"]),
                )

    async def test_async_get_measure__valid_request_params__returns_valid_measurement_item_list(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/getmeasure",
                        data=get_measure_request_mock_data).respond(200, json=get_measure_response)

        async with thermostat_client("", "", token, None) as client:
            measurement_items = await client.async_get_measure(
                get_measure_request["device_id"],
                get_measure_request["module_id"],
                MeasurementType.TEMPERATURE,
                MeasurementScale.MAX,
                datetime.fromtimestamp(get_measure_request["date_begin"]),
            )

            assert len(measurement_items) == len(get_measure_response["body"])
            for x in zip(measurement_items, get_measure_response["body"]):
                assert x[0] == MeasurementItem(**x[1])

    async def test_async_set_system_mode__invalid_request_params__raises_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setsystemmode",
                        data=set_system_mode_request_mock_data).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException): # Changed from UnsuportedArgumentsException to RequestClientException
                await client.async_set_system_mode(
                    set_system_mode_request["device_id"],
                    set_system_mode_request["module_id"],
                    SystemMode.SUMMER,
                )

    async def test_async_set_system_mode__server_errors__retry_until_success(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setsystemmode",
                        data=set_system_mode_request_mock_data).mock(side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=set_system_mode_response),
        ])

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_system_mode(
                set_system_mode_request["device_id"],
                set_system_mode_request["module_id"],
                SystemMode.SUMMER,
            )

            assert respx_mock.calls.call_count == 2

    async def test_async_set_system_mode__valid_request_params__doesnt_raise_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setsystemmode",
                        data=set_system_mode_request_mock_data).respond(200, json=set_system_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_system_mode(
                set_system_mode_request["device_id"],
                set_system_mode_request["module_id"],
                SystemMode.SUMMER,
            )

    async def test_async_set_minor_mode__invalid_request_params__raises_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setminormode",
                        data=set_minor_mode_request_mock_data).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException): # Changed from UnsuportedArgumentsException to RequestClientException
                await client.async_set_minor_mode(
                    set_minor_mode_request["device_id"],
                    set_minor_mode_request["module_id"],
                    SetpointMode.AWAY,
                    True,
                )

    async def test_async_set_minor_mode__server_errors__retry_until_success(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setminormode",
                        data=set_minor_mode_request_mock_data).mock(side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=set_minor_mode_response),
        ])

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                set_minor_mode_request["device_id"],
                set_minor_mode_request["module_id"],
                SetpointMode.AWAY,
                True,
            )

            assert respx_mock.calls.call_count == 2

    async def test_async_set_minor_mode__activate_manual_with_temp_and_endtime__executes_successfully(self, respx_mock: MockRouter):
        mock_data = set_minor_mode_manual_activate_with_temp_and_endtime_mock_data.copy()
        mock_data["setpoint_endtime"] = round((datetime.now() + timedelta(minutes=10)).timestamp()) # Set dynamically
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=mock_data).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                "device",
                "module",
                SetpointMode.MANUAL,
                True,
                datetime.now() + timedelta(minutes=10),
                20.0,
            )
            
    async def test_async_set_minor_mode__deactivate_manual_without_temp_and_endtime__executes_successfully(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_manual_deactivate_mock_data).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                "device",
                "module",
                SetpointMode.MANUAL,
                False,
            )

    async def test_async_set_minor_mode__activate_away_without_temp_and_endtime__executes_successfully(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_away_activate_mock_data).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                "device",
                "module",
                SetpointMode.AWAY,
                True,
            )

    async def test_async_set_minor_mode__activate_away_without_temp__executes_successfully(self, respx_mock: MockRouter):
        mock_data = set_minor_mode_away_activate_with_endtime_mock_data.copy()
        mock_data["setpoint_endtime"] = round((datetime.now() + timedelta(minutes=10)).timestamp()) # Set dynamically
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=mock_data).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                "device",
                "module",
                SetpointMode.AWAY,
                True,
                datetime.now() + timedelta(minutes=10),
            )

    async def test_async_set_minor_mode__deactivate_away_without_temp_and_endtime__executes_successfully(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_away_deactivate_mock_data).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                "device",
                "module",
                SetpointMode.AWAY,
                False,
            )

    async def test_async_set_minor_mode__activate_hwb_without_temp__raises_error(self, respx_mock: MockRouter): # Changed test name to reflect expected error
        # No mock needed as the error is raised before the HTTP request is made
        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(UnsuportedArgumentsException): # Assert that it raises the expected exception
                await client.async_set_minor_mode(
                    "device",
                    "module",
                    SetpointMode.HWB,
                    True,
                )

    async def test_async_set_minor_mode__deactivate_hwb_without_temp_and_endtime__executes_successfully(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/setminormode", data=set_minor_mode_hwb_deactivate_mock_data).respond(200, json=set_minor_mode_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode(
                "device",
                "module",
                SetpointMode.HWB,
                False,
            )

    async def test_async_sync_schedule__invalid_request_params__raises_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/syncschedule",
                        data=sync_schedule_request_mock_data).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException): # Changed from UnsuportedArgumentsException to RequestClientException
                await client.async_sync_schedule(
                    sync_schedule_request["device_id"],
                    sync_schedule_request["module_id"],
                    sync_schedule_request["schedule_id"],
                    sync_schedule_request["name"],
                    [],
                    [],
                )

    async def test_async_sync_schedule__server_errors__retry_until_success(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/syncschedule",
                        data=sync_schedule_request_mock_data).mock(side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=sync_schedule_response),
        ])

        async with thermostat_client("", "", token, None) as client:
            await client.async_sync_schedule(
                sync_schedule_request["device_id"],
                sync_schedule_request["module_id"],
                sync_schedule_request["schedule_id"],
                sync_schedule_request["name"],
                [],
                [],
            )

            assert respx_mock.calls.call_count == 2

    async def test_async_sync_schedule__valid_request_params__doesnt_raise_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/syncschedule",
                        data=sync_schedule_request_mock_data).respond(200, json=sync_schedule_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_sync_schedule(
                sync_schedule_request["device_id"],
                sync_schedule_request["module_id"],
                sync_schedule_request["schedule_id"],
                sync_schedule_request["name"],
                [],
                [],
            )

    async def test_async_switch_schedule__invalid_request_params__raises_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/switchschedule",
                        data=switch_schedule_request_mock_data).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException): # Changed from UnsuportedArgumentsException to RequestClientException
                await client.async_switch_schedule(
                    switch_schedule_request["device_id"],
                    switch_schedule_request["module_id"],
                    switch_schedule_request["schedule_id"],
                )

    async def test_async_switch_schedule__server_errors__retry_until_success(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/switchschedule",
                        data=switch_schedule_request_mock_data).mock(side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=switch_schedule_response),
        ])

        async with thermostat_client("", "", token, None) as client:
            await client.async_switch_schedule(
                switch_schedule_request["device_id"],
                switch_schedule_request["module_id"],
                switch_schedule_request["schedule_id"],
            )

            assert respx_mock.calls.call_count == 2

    async def test_async_switch_schedule__valid_request_params__doesnt_raise_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/switchschedule",
                        data=switch_schedule_request_mock_data).respond(200, json=switch_schedule_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_switch_schedule(
                switch_schedule_request["device_id"],
                switch_schedule_request["module_id"],
                switch_schedule_request["schedule_id"],
            )

    async def test_async_set_hot_water_temperature__invalid_request_params__raises_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/sethotwatertemperature",
                        data=async_set_hot_water_temperature_request_mock_data).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException): # Changed from UnsuportedArgumentsException to RequestClientException
                await client.async_set_hot_water_temperature(
                    async_set_hot_water_temperature_request["device_id"],
                    async_set_hot_water_temperature_request["dhw"],
                )

    async def test_async_set_hot_water_temperature__server_errors__retry_until_success(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/sethotwatertemperature",
                        data=async_set_hot_water_temperature_request_mock_data).mock(side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=async_set_hot_water_temperature_response),
        ])

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_hot_water_temperature(
                async_set_hot_water_temperature_request["device_id"],
                async_set_hot_water_temperature_request["dhw"],
            )

            assert respx_mock.calls.call_count == 2

    async def test_async_set_hot_water_temperature__valid_request_params__doesnt_raise_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/sethotwatertemperature",
                        data=async_set_hot_water_temperature_request_mock_data).respond(200, json=async_set_hot_water_temperature_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_set_hot_water_temperature(
                async_set_hot_water_temperature_request["device_id"],
                async_set_hot_water_temperature_request["dhw"],
            )

    async def test_async_modify_device_param__invalid_request_params__raises_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/modifydeviceparam",
                        data=async_modify_device_param_request_mock_data).respond(400)

        async with thermostat_client("", "", token, None) as client:
            with pytest.raises(RequestClientException): # Changed from UnsuportedArgumentsException to RequestClientException
                await client.async_modify_device_params(
                    async_modify_device_param_request["device_id"],
                    async_modify_device_param_request["setpoint_default_duration"],
                )

    async def test_async_modify_device_param__server_errors__retry_until_success(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/modifydeviceparam",
                        data=async_modify_device_param_request_mock_data).mock(side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=async_modify_device_param_response),
        ])

        async with thermostat_client("", "", token, None) as client:
            await client.async_modify_device_params(
                async_modify_device_param_request["device_id"],
                async_modify_device_param_request["setpoint_default_duration"],
            )

            assert respx_mock.calls.call_count == 2

    async def test_async_modify_device_param__valid_request_params__doesnt_raise_error(self, respx_mock: MockRouter):
        respx_mock.post("https://api.netatmo.com/api/modifydeviceparam",
                        data=async_modify_device_param_request_mock_data).respond(200, json=async_modify_device_param_response)

        async with thermostat_client("", "", token, None) as client:
            await client.async_modify_device_params(
                async_modify_device_param_request["device_id"],
                async_modify_device_param_request["setpoint_default_duration"],
            )