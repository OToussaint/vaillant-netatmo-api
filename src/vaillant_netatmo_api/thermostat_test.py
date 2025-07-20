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

@pytest.mark.asyncio
class TestThermostatAllMocked:
    @pytest.fixture(autouse=True)
    def setup_respx(self, respx_mock: MockRouter):
        # Mock all endpoints needed for all tests
        respx_mock.post("https://app.netatmo.net/api/homesdata").respond(200, json=homesdata_response)
        respx_mock.post("https://app.netatmo.net/api/getthermostatsdata").respond(200, json=get_thermostats_data_response)
        respx_mock.post("https://app.netatmo.net/api/getmeasure").respond(200, json=get_measure_response)
        respx_mock.post("https://app.netatmo.net/api/setsystemmode").respond(200, json=set_system_mode_response)
        respx_mock.post("https://app.netatmo.net/api/setminormode").respond(200, json=set_minor_mode_response)
        respx_mock.post("https://app.netatmo.net/api/syncschedule").respond(200, json=sync_schedule_response)
        respx_mock.post("https://app.netatmo.net/api/switchschedule").respond(200, json=switch_schedule_response)
        respx_mock.post("https://app.netatmo.net/api/sethotwatertemperature").respond(200, json=async_set_hot_water_temperature_response)
        respx_mock.post("https://app.netatmo.net/api/modifydeviceparam").respond(200, json=async_modify_device_param_response)
        respx_mock.post("https://app.netatmo.net/oauth2/token").respond(200, json=refresh_token_response)

    async def test_async_get_thermostats_data(self):
        async with thermostat_client("", "", token, None) as client:
            devices = await client.async_get_thermostats_data()
            assert isinstance(devices, list)
            assert all(isinstance(d, Device) for d in devices)

    async def test_async_get_measure(self):
        async with thermostat_client("", "", token, None) as client:
            measurement_items = await client.async_get_measure(
                "device", "module", MeasurementType.TEMPERATURE, MeasurementScale.MAX, datetime.fromtimestamp(1642252768)
            )
            assert isinstance(measurement_items, list)
            assert all(isinstance(m, MeasurementItem) for m in measurement_items)

    async def test_async_set_system_mode(self):
        async with thermostat_client("", "", token, None) as client:
            await client.async_set_system_mode("device", "module", SystemMode.SUMMER)

    async def test_async_set_minor_mode(self):
        async with thermostat_client("", "", token, None) as client:
            await client.async_set_minor_mode("device", "module", SetpointMode.AWAY, True)

    async def test_async_sync_schedule(self):
        async with thermostat_client("", "", token, None) as client:
            await client.async_sync_schedule(
                "device", "module", "program_id", "name",
                [Zone(**{"temp": 20, "id": 0, "hw": True})],
                [TimeSlot(**{"id": 0, "m_offset": 0})]
            )

    async def test_async_switch_schedule(self):
        async with thermostat_client("", "", token, None) as client:
            await client.async_switch_schedule("device", "module", "program_id")

    async def test_async_set_hot_water_temperature(self):
        async with thermostat_client("", "", token, None) as client:
            await client.async_set_hot_water_temperature("device", 50)

    async def test_async_modify_device_param(self):
        async with thermostat_client("", "", token, None) as client:
            await client.async_modify_device_params("device", 120)

    async def test_async_get_home_data(self):
        async with thermostat_client("", "", token, None) as client:
            homes = await client.async_get_home_data()
            assert isinstance(homes, list)
            assert all(hasattr(h, "home_id") for h in homes)
