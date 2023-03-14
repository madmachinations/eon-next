#!/usr/bin/env python3

import aiohttp
import datetime

METER_TYPE_GAS = "gas"
METER_TYPE_ELECTRIC = "electricity"
METER_TYPE_UNKNOWN = "unknown"


class EonNext:

    def __init__(self):
        self.username = ""
        self.password = ""
        self.__reset_authentation()
        self.__reset_accounts()
    

    def _json_contains_key_chain(self, data: dict, key_chain: list) -> bool:
        for key in key_chain:
            if key in data:
                data = data[key]
            else:
                return False
        return True
    

    def __current_timestamp(self) -> int:
        now = datetime.datetime.now()
        return int(datetime.datetime.timestamp(now))


    def __reset_authentation(self):
        self.auth = {
            "issued": None,
            "token": {
                "token": None,
                "expires": None
            },
            "refresh": {
                "token": None,
                "expires": None
            }
        }
    
    def __store_authentication(self, kraken_token: dict):
        self.auth = {
            "issued": kraken_token['payload']['iat'],
            "token": {
                "token": kraken_token['token'],
                "expires": kraken_token['payload']['exp']
            },
            "refresh": {
                "token": kraken_token['refreshToken'],
                "expires": kraken_token['refreshExpiresIn']
            }
        }
    

    def __auth_token_is_valid(self) -> bool:
        if self.auth['token']['token'] == None:
            return False
        
        if self.auth['token']['expires'] <= self.__current_timestamp():
            return False
        
        return True
    

    def __refresh_token_is_valid(self) -> bool:
        if self.auth['refresh']['token'] == None:
            return False
        
        if self.auth['refresh']['expires'] <= self.__current_timestamp():
            return False
        
        return True
    

    async def __auth_token(self) -> str:
        if self.__auth_token_is_valid() == False:
            if self.__refresh_token_is_valid() == True:
                await self.__login_with_refresh_token()
            else:
                await self.login_with_username_and_password()
        
        if self.__auth_token_is_valid() == False:
            raise Exception("Unable to authenticate")

        return self.auth['token']['token']
    

    async def _graphql_post(self, operation: str, query: str, variables: dict={}, authenticated: bool = True) -> dict:
        use_headers = {}

        if authenticated == True:
            use_headers['authorization'] = "JWT " + await self.__auth_token()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.eonnext-kraken.energy/v1/graphql/",
                json={"operationName": operation, "variables": variables, "query": query},
                headers=use_headers
            ) as response:
                return await response.json()
    

    async def login_with_username_and_password(self, username: str, password: str, initialise: bool = True) -> bool:
        self.username = username
        self.password = password
        
        result = await self._graphql_post(
            "loginEmailAuthentication",
            "mutation loginEmailAuthentication($input: ObtainJSONWebTokenInput!) {obtainKrakenToken(input: $input) {    payload    refreshExpiresIn    refreshToken    token    __typename}}",
            {
                "input": {
                    "email": self.username,
                    "password": self.password
                }
            },
            False
        )

        if self._json_contains_key_chain(result, ["data", "obtainKrakenToken", "token"]) == True:
            self.__store_authentication(result['data']['obtainKrakenToken'])
            if initialise == True:
                await self.__init_accounts()
            return True
        else:
            self.__reset_authentation()
            return False
    

    async def login_with_refresh_token(self, token: str) -> bool:
        self.auth['refresh']['token'] = token
        return await self.__login_with_refresh_token(True)
    

    async def __login_with_refresh_token(self, initialise: bool = False) -> bool:
        result = await self._graphql_post(
            "refreshToken",
            "mutation refreshToken($input: ObtainJSONWebTokenInput!) {  obtainKrakenToken(input: $input) {    payload    refreshExpiresIn    refreshToken    token    __typename  }}",
            {
                "input": {
                    "refreshToken": self.auth['refresh']['token']
                }
            },
            False
        )

        if self._json_contains_key_chain(result, ["data", "obtainKrakenToken", "token"]) == True:
            self.__store_authentication(result['data']['obtainKrakenToken'])
            if initialise == True:
                await self.__init_accounts()
            return True
        else:
            self.__reset_authentation()
            return False
    

    def __reset_accounts(self):
        self.accounts = []
    

    async def __get_account_numbers(self) -> list:
        result = await self._graphql_post(
            "headerGetLoggedInUser",
            "query headerGetLoggedInUser {\n  viewer {\n    accounts {\n      ... on AccountType {\n        applications(first: 1) {\n          edges {\n            node {\n              isMigrated\n              migrationSource\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        balance\n        id\n        number\n        __typename\n      }\n      __typename\n    }\n    id\n    preferredName\n    __typename\n  }\n}\n"
        )
        
        if self._json_contains_key_chain(result, ["data", "viewer", "accounts"]) == False:
            raise Exception("Unable to load energy accounts")

        found = []
        for account_entry in result['data']['viewer']['accounts']:
            found.append(account_entry['number'])

        return found
    

    async def __init_accounts(self):
        if len(self.accounts) == 0:
            for account_number in await self.__get_account_numbers():

                account = EnergyAccount(self, account_number)
                await account._load_meters()

                self.accounts.append(account)




class EnergyAccount:

    def __init__(self, api: EonNext, account_number: str):
        self.api = api
        self.account_number = account_number
    

    async def _load_meters(self):
        result = await self.api._graphql_post(
            "getAccountMeterSelector",
            "query getAccountMeterSelector($accountNumber: String!, $showInactive: Boolean!) {\n  properties(accountNumber: $accountNumber) {\n    ...MeterSelectorPropertyFields\n    __typename\n  }\n}\n\nfragment MeterSelectorPropertyFields on PropertyType {\n  __typename\n  electricityMeterPoints {\n    ...MeterSelectorElectricityMeterPointFields\n    __typename\n  }\n  gasMeterPoints {\n    ...MeterSelectorGasMeterPointFields\n    __typename\n  }\n  id\n  postcode\n}\n\nfragment MeterSelectorElectricityMeterPointFields on ElectricityMeterPointType {\n  __typename\n  id\n  meters(includeInactive: $showInactive) {\n    ...MeterSelectorElectricityMeterFields\n    __typename\n  }\n}\n\nfragment MeterSelectorElectricityMeterFields on ElectricityMeterType {\n  __typename\n  activeTo\n  id\n  registers {\n    id\n    name\n    __typename\n  }\n  serialNumber\n}\n\nfragment MeterSelectorGasMeterPointFields on GasMeterPointType {\n  __typename\n  id\n  meters(includeInactive: $showInactive) {\n    ...MeterSelectorGasMeterFields\n    __typename\n  }\n}\n\nfragment MeterSelectorGasMeterFields on GasMeterType {\n  __typename\n  activeTo\n  id\n  registers {\n    id\n    name\n    __typename\n  }\n  serialNumber\n}\n",
            {
                "accountNumber": self.account_number,
                "showInactive": False
            }
        )
        
        if self.api._json_contains_key_chain(result, ["data", "properties"]) == False:
            raise Exception("Unable to load energy meters for account " + self.account_number)
        
        self.meters = []
        for property in result['data']['properties']:

            for electricity_point in property['electricityMeterPoints']:
                for meter_config in electricity_point['meters']:
                    meter = ElectricityMeter(self, meter_config['id'], meter_config['serialNumber'])
                    self.meters.append(meter)
            
            for gas_point in property['gasMeterPoints']:
                for meter_config in gas_point['meters']:
                    meter = GasMeter(self, meter_config['id'], meter_config['serialNumber'])
                    self.meters.append(meter)




class EnergyMeter:

    def __init__(self, account: EnergyAccount, meter_id: str, serial: str):
        self.account = account
        self.api = account.api

        self.last_updated = None

        self.type = METER_TYPE_UNKNOWN
        self.meter_id = meter_id
        self.serial = serial

        self.latest_reading = None
        self.latest_reading_date = None
    

    def get_type(self) -> str:
        return self.type
    

    def get_serial(self) -> str:
        return self.serial
    

    def _should_update(self) -> bool:
        if self.last_updated == None:
            return True
        
        now = datetime.datetime.now()
        if now.strftime("%d") != self.last_updated.strftime("%d"):
            if now.hour >= 7:
                return True
        
        return False


    def _convert_datetime_str_to_date(self, datetime_str: str) -> datetime.date:
        date_chunks = str(datetime_str.split("T")[0]).split("-")
        return datetime.date(int(date_chunks[0]), int(date_chunks[1]), int(date_chunks[2]))
    

    async def _update(self):
        pass


    async def update(self):
        if self._should_update() == True:
            await self._update()
    

    async def has_reading(self) -> bool:
        await self.update()
        if self.latest_reading != None:
            return True
        return False


    async def get_latest_reading(self) -> int:
        await self.update()
        return self.latest_reading


    async def get_latest_reading_date(self) -> datetime.date:
        await self.update()
        return self.latest_reading_date



class ElectricityMeter(EnergyMeter):

    def __init__(self, account: EnergyAccount, meter_id: str, serial: str):
        super().__init__(account, meter_id, serial)
        self.type = METER_TYPE_ELECTRIC
    

    async def _update(self):
        result = await self.api._graphql_post(
            "meterReadingsHistoryTableElectricityReadings",
            "query meterReadingsHistoryTableElectricityReadings($accountNumber: String!, $cursor: String, $meterId: String!) {\n  readings: electricityMeterReadings(\n    accountNumber: $accountNumber\n    after: $cursor\n    first: 12\n    meterId: $meterId\n  ) {\n    edges {\n      ...MeterReadingsHistoryTableElectricityMeterReadingConnectionTypeEdge\n      __typename\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment MeterReadingsHistoryTableElectricityMeterReadingConnectionTypeEdge on ElectricityMeterReadingConnectionTypeEdge {\n  node {\n    id\n    readAt\n    readingSource\n    registers {\n      name\n      value\n      __typename\n    }\n    source\n    __typename\n  }\n  __typename\n}\n",
            {
                "accountNumber": self.account.account_number,
                "cursor": "",
                "meterId": self.meter_id
            }
        )

        if self.api._json_contains_key_chain(result, ["data", "readings"]) == False:
            raise Exception("Unable to load readings for meter " + self.serial)

        readings = result['data']['readings']['edges']
        if len(readings) > 0:
            self.latest_reading = round(float(readings[0]['node']['registers'][0]['value']))
            self.latest_reading_date = self._convert_datetime_str_to_date(readings[0]['node']['readAt'])
            self.last_updated = datetime.datetime.now()



class GasMeter(EnergyMeter):

    def __init__(self, account: EnergyAccount, meter_id: str, serial: str):
        super().__init__(account, meter_id, serial)
        self.type = METER_TYPE_GAS
    

    async def _update(self):
        result = await self.api._graphql_post(
            "meterReadingsHistoryTableGasReadings",
            "query meterReadingsHistoryTableGasReadings($accountNumber: String!, $cursor: String, $meterId: String!) {\n  readings: gasMeterReadings(\n    accountNumber: $accountNumber\n    after: $cursor\n    first: 12\n    meterId: $meterId\n  ) {\n    edges {\n      ...MeterReadingsHistoryTableGasMeterReadingConnectionTypeEdge\n      __typename\n    }\n    pageInfo {\n      endCursor\n      hasNextPage\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment MeterReadingsHistoryTableGasMeterReadingConnectionTypeEdge on GasMeterReadingConnectionTypeEdge {\n  node {\n    id\n    readAt\n    readingSource\n    registers {\n      name\n      value\n      __typename\n    }\n    source\n    __typename\n  }\n  __typename\n}\n",
            {
                "accountNumber": self.account.account_number,
                "cursor": "",
                "meterId": self.meter_id
            }
        )

        if self.api._json_contains_key_chain(result, ["data", "readings"]) == False:
            raise Exception("Unable to load readings for meter " + self.serial)

        readings = result['data']['readings']['edges']
        if len(readings) > 0:
            self.latest_reading = round(float(readings[0]['node']['registers'][0]['value']))
            self.latest_reading_date = self._convert_datetime_str_to_date(readings[0]['node']['readAt'])
            self.last_updated = datetime.datetime.now()
    

    async def get_latest_reading_kwh(self) -> int:
        m3 = await self.get_latest_reading()
        gas_caloric_value = 38

        kwh = m3 * 1.02264
        kwh = kwh * gas_caloric_value
        kwh = kwh / 3.6

        return round(kwh)
