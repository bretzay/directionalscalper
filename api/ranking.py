import time
from urllib.parse import urlencode
import random
import fnmatch
import json
import threading
import requests
from dataclasses import dataclass, field

import api.api_handler as api_handler
from utils.logger import Logger

logging = Logger(logger_name= "api_handler", filename= "Api.log", stream= True,level= "debug")

class HTTPRequestError(Exception):
    def __init__(self, url, code, msg=None):
        self.url = url
        self.code = code
        self.msg = msg if msg else "Unknown error"

    def __str__(self):
        return f"HTTP Request to {self.url} failed with code {self.code}: {self.msg}"


@dataclass
class Ranking_handler:
    api: api_handler.ApiConfig = field(init= True, repr= False)
    config: api_handler.Config = field(init= True, repr= False)
    max_usd_value: int = field(init= False)
    blacklist: list = field(default_factory= list, init= False)
    whitelist: list = field(default_factory= list, init= False)
    rotator_url: str = field(init= False, repr= False)
    cache_lasting_time: int = field(default= 60, init= False, repr= False)
    cached_date: float = field(default= 0, init= False, repr= False)
    cached_symbol: list = field(init= False, repr= True, default_factory= list)
    caching_symbol: list = field(init= False, repr= False, default_factory= list)

    def __post_init__(self):
        self.max_usd_value = self.config.coin_filters.max_usd_value
        self.blacklist = self.config.coin_filters.blacklist
        self.whitelist = self.config.coin_filters.whitelist
        self.rotator_url = f"{self.api.url}{self.api.data_source_exchange.replace('_', '')}.json"

        threading.Thread(target= self.get_rotating_symbols, daemon= True).start()
    def get_rotating_symbols(self):
        #while True:
        if self.cached_symbol and not self._is_cache_expired():
            time.sleep(self.cache_lasting_time)
            #continue
            return
        try:
            logging.info(f"Sending request to {self.rotator_url}")
            header, raw_json = self.send_public_request()
            if not isinstance(raw_json, list):
                logging.warning("Unexpected data format. Expected a list of assets.")
                #continue
                return
            logging.info(f"Received {len(raw_json)} assets from API")
            self.caching_symbol = [
                symbol
                for asset in raw_json if ( 
                symbol := asset.get("Asset", ""), 
                usd_price := asset.get("Price", float('inf')))
                and self._is_blacklist(symbol)
                and self._is_whitelist(symbol)
                and self._is_max_usd_value(symbol, usd_price)
            ]
            logging.info(f"Returning {len(self.caching_symbol)} symbols")
            if self.caching_symbol:
                self.cached_symbol = self.caching_symbol.copy()
                self.caching_symbol.clear()
                self.cached_date = time.time()
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed: {e}")
        except json.decoder.JSONDecodeError as e:
            logging.warning(f"Failed to parse JSON: {e}. Response: {raw_json}")
        except Exception as e:
            logging.warning(f"Unexpected error occurred: {e}")

    def _is_blacklist(self, symbol) -> str | None:
        if self.blacklist and any(fnmatch.fnmatch(symbol, pattern) for pattern in self.blacklist):
            logging.debug(f"Skipping {symbol} as it's in blacklist")
            return
        return symbol

    def _is_whitelist(self, symbol) -> str | None:
        if self.whitelist and symbol not in self.whitelist:
            logging.debug(f"Skipping {symbol} as it's not in whitelist")
            return
        return symbol

    def _is_max_usd_value(self, symbol, usd_price) -> str | None:
        if self.max_usd_value is not None and usd_price > self.max_usd_value:
            logging.debug(f"Skipping {symbol} as its USD price {usd_price} is greater than the max allowed {self.max_usd_value}")
            return
        logging.debug(f"Processing symbol {symbol} of price {usd_price}USDT")
        return symbol

    def _is_cache_expired(self):
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

