from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar



import sys
# Add the project root to the PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


from utils.logger import Logger
from utils.util import load_json
from config import Config
import api.ranking as ranking
# TODO: change all get_auto_rotate_symbols() of the old manager.py to the new API_Handler.ranking.rotator_list or something like that when it is done.
# TODO: Change all the min_qty_threshold to max_min_qty to be clearer?


logging = Logger(logger_name= "api_handler", filename= "Api.log", stream= True,level= "debug")


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
        data_source_exchange: str = field(default= account_file["ranking"]["data_source_exchange"], repr=False)
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
        if not self.data_source_exchange:
            self.data_source_exchange = "bybit"
        self.account = Account_credential(self.exchange_name, self.account_name, self.account_file["exchanges"])

# All this is just for tests purposes
def main():
    config: Config = Config("configs/config.json")
    apiConfig: ApiConfig = ApiConfig("bybit", "test_acc")
    ranking_handler: ranking.Ranking_handler = ranking.Ranking_handler(apiConfig, config)
    new_list = []
    print(new_list)
    while True:
        try:
            if not sorted(new_list) == sorted(ranking_handler.cached_symbol):
                print(f"The list {new_list} is different of {ranking_handler.cached_symbol}, changing its value.")
                new_list = ranking_handler.cached_symbol.copy()
                print(f"List {new_list} updated.")
        except KeyboardInterrupt:
            print("You stopped the bot")
            exit()

if __name__ == "__main__":
    main()