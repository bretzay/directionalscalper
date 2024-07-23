from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar
import time
from urllib.parse import urlencode
import random
import fnmatch


import requests
# I know It's weird, but I just want to be able to test my code from the main.py
# The try catch can be deleted and back to normal when we do not need to test api handler directly.
#try:
#    from utils.logger import Logger
#    from utils.util import load_json
#    from config import Config
#except ImportError:
import sys
# Add the project root to the PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
from utils.logger import Logger
from utils.util import load_json
from config import Config
# TODO: change all get_auto_rotate_symbols() of the old manager.py to the new API_Handler.ranking.rotator_list or something like that when it is done.
# TODO: Change all the min_qty_threshold to max_min_qty to be clearer?


logging = Logger(logger_name= "api_handler", filename= "Api.log", stream= True,level= "debug")


@dataclass
class Ranking_list:
    coin: Ranking_data

@dataclass
class Ranking_data:
    symbol: str

# Will probably return None at the end, BUT will have a function like .get_rotator() 
# As it is already in manager.py, to gather the rotator symbols kept in cache waiting to be seen.
class Ranking_handler:
    def __init__(self, apiConfig) -> None:
        self.api: ApiConfig = apiConfig
        
        self.rotator_url: str = f"https://api.quantumvoid.org/volumedata/rotatorsymbols_{self.api.data_source_exchange.replace('_', '')}.json"
        self.caching_retries: int = 5
        self.cache_lasting_time: int = 5
        self.cached_date : float = 0
        self.cached_symbol: list = field(default_factory=list)



    def get_rotating_symbols(self):
        if self.cached_symbol and not self.is_cache_expired():
            return self.cached_symbol
        
        for retry in range(self.caching_retries):
            delay = min(58, 2**retry) # Maximum 58 seconds per retry

            try:
                logging.info(f"Sending request to {self.rotator_url} (Attempt: {retry+1})")
                header, raw_json = self.send_public_request()

                if not isinstance(raw_json, list):
                    logging.warning("Unexpected data format. Expected a list of assets.")
                    continue
                
                logging.info(f"Received {len(raw_json)} assets from API")
                    
                for asset in raw_json:
                    symbol = asset.get("Asset", "")
                    min_qty = asset.get("Min qty", 0)
                    usd_price = asset.get("Price", float('inf')) 
                    
                    logging.info(f"Processing symbol {symbol} with min_qty {min_qty} and USD price {usd_price}")
                    if blacklist and any(fnmatch.fnmatch(symbol, pattern) for pattern in blacklist):
                        logging.debug(f"Skipping {symbol} as it's in blacklist")
                        continue
                    if whitelist and symbol not in whitelist:
                        logging.debug(f"Skipping {symbol} as it's not in whitelist")
                        continue
                    # Check against the max_usd_value, if provided
                    if max_usd_value is not None and usd_price > max_usd_value:
                        logging.debug(f"Skipping {symbol} as its USD price {usd_price} is greater than the max allowed {max_usd_value}")
                        continue
                    logging.debug(f"Processing symbol {symbol} with min_qty {min_qty} and USD price {usd_price}")
                    if min_qty_threshold is None or min_qty <= min_qty_threshold:
                        symbols.append(symbol)
                logging.info(f"Returning {len(symbols)} symbols")
                
                # If successfully fetched, update the cache and its expiry time
                if symbols:
                    self.rotator_symbols_cache = symbols
                    self.rotator_symbols_cache_expiry = datetime.now() + timedelta(seconds=self.cache_life_seconds)
                return symbols

                    
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request failed: {e}")
            except json.decoder.JSONDecodeError as e:
                logging.warning(f"Failed to parse JSON: {e}. Response: {raw_json}")
            except Exception as e:
                logging.warning(f"Unexpected error occurred: {e}")

            # Wait before the next retry
            if retry < max_retries - 1:
                time.sleep(delay)
        
        # Return cached symbols if all retries fail
        logging.warning(f"Couldn't fetch rotator symbols after {max_retries} attempts. Using cached symbols.")
        return self.rotator_symbols_cache or []


    def is_cache_expired(self):
        return time.time() > self.cached_date + self.cache_lasting_time

    def send_public_request(
        self,
        method: str = "GET",
        url_path: str | None = None,
        payload: dict | None = None,
        json_in: dict | None = None,
        json_out: bool = True,
        max_retries: int = 10000,
        base_delay: float = 0.5  # base delay for exponential backoff
    ):
        if url_path is not None:
            self.rotator_url += url_path
        if payload is None:
            payload = {}
        query_string = urlencode(payload, True)
        if query_string:
            self.rotator_url += "?" + query_string

        attempt = 0
        while attempt < max_retries:
            try:
                response = requests.request(method, self.rotator_url, json=json_in, timeout=30)
                if not json_out:
                    return response.headers, response.text

                json_response = response.json()
                if response.status_code != 200:
                    raise HTTPRequestError(self.rotator_url, response.status_code, json_response.get("msg"))

                return response.headers, json_response
            except requests.exceptions.ConnectionError as e:
                logging.warning(f"Connection error on {self.rotator_url}: {e}")
            except requests.exceptions.Timeout as e:
                logging.warning(f"Request timed out for {self.rotator_url}: {e}")
            except requests.exceptions.TooManyRedirects as e:
                logging.warning(f"Too many redirects for {self.rotator_url}: {e}")
            except requests.exceptions.JSONDecodeError as e:
                logging.warning(f"JSON decode error at {self.rotator_url}: {e}")
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request exception at {self.rotator_url}: {e}")
            except HTTPRequestError as e:
                logging.warning(str(e))

            attempt += 1
            # Adding increased jitter
            sleep_time = base_delay * (2 ** min(attempt, 7)) + random.uniform(0, 1)  # Increased jitter up to 1 second
            time.sleep(min(sleep_time, 60))  # Still capping the maximum delay to prevent extreme wait times


        logging.error(f"All retries failed for {self.rotator_url} after {max_retries} attempts")
        return None, None  # Indicating that no data could be retrieved after retries
        

@dataclass
class Account_credential:
    exchange_name: str
    account_name: str
    exchanges_list: list = field(repr= False)
    
    def __post_init__(self):
        exchange_data: list[dict[str,str]] = self.find_exchange()
        self.credentials: dict[str,str] = field(default_factory=dict[str,str], repr=True)
        self.credentials = self.get_credentials(exchange_data)

    def get_credentials(self, exchange_data) -> dict[str,str] :
        """Create a dictionary with the api key and the api secret."""
        try:
            creds: dict[str,str] = {
            key: value
            for key, value in exchange_data.items()
            if key == "api_key" or key == "api_secret"
        }
            if creds.__len__() != 2:
                raise ValueError
            return creds
        
        except ValueError:
            logging.error(f"There is an error in account.json. Only {creds.__len__()} found, 2 are needed.")
            exit()
        
    def find_exchange(self):
        """Search the exchange that has the same name and account_name as the given data in the creation of ApiConfig."""
        try:
            return [
                exchange for exchange in self.exchanges_list 
                if exchange["name"] == self.exchange_name
                and exchange["account_name"] == self.account_name
            ][0]
        except IndexError:
            logging.error("Could not find the duo exchange_name/account_name. Please verify your account.json or your inputs at restart.")
            exit()

@dataclass
class ApiConfig:
    # Credentials identification
    try: 
        exchange_name: str
        account_name: str
        account_file: ClassVar[dict] = load_json(f"{Path(__file__).parent.parent}/configs/account.json")
        # Places where to gather data for ranking (remote or local)
        data_source_exchange: ClassVar[str] = account_file["ranking"]["data_source_exchange"]
        mode: ClassVar[str] = account_file["ranking"]["mode"] 
        url: ClassVar[str] = account_file["ranking"]["url"]
        local_path: ClassVar[str] = account_file["ranking"]["local_path"]
    except FileNotFoundError:
        logging.error("Account.json was not found, please verify that your file is stored as: /directionalscalper/configs/account.json")
        exit()
    except ValueError as e:
        logging.error(f"A value was awaited but was not available, please verify your account.json file.\n{e}")
        exit()
    except Exception as e:
        logging.error(f"There was an unexpected error while initializing ApiConfig, please share it to developpers to make an error handling segment.\n{e}")
        exit()

    def __post_init__(self):
        self.account = Account_credential(self.exchange_name, self.account_name, self.account_file["exchanges"])

class HTTPRequestError(Exception):
    def __init__(self, url, code, msg=None):
        self.url = url
        self.code = code
        self.msg = msg if msg else "Unknown error"

    def __str__(self):
        return f"HTTP Request to {self.url} failed with code {self.code}: {self.msg}"


def test_functions(parameter, functions: list):
    new_list: list = [function(parameter) for function in functions]
    print(sum(new_list))

def out1(parameter):
    print(parameter)
    return True
def out2(parameter):
    print("test2")
    return True
def out3(parameter):
    print("test3")
    return False
def out4(parameter):
    print("tes4")
    return False

def main():
    config = Config("configs/config.json")

if __name__ == "__main__":
    main()