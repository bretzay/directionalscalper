from dataclasses import dataclass, field
from typing import ClassVar
from pathlib import Path

from utils.logger import Logger
from utils.utils import load_json

logging = Logger(logger_name= "api_handler", filename= "Api.log", stream= True,level= "debug")

AUTHORIZED_MARKET_TYPE: list[str] = ["swap", "spot"]

@dataclass
class ApiConfig:
    try: 
        # Data used in the class
        account_file: ClassVar[dict] = load_json(f"{Path(__file__).parent.parent}/configs/account.json")
        # Credentials identification
        exchange_name: str
        account_name: str
        exchange: dict[str, str] = field(repr= False, init= False)
        credentials: dict[str, str] = field(default_factory=dict[str,str], init= False, repr=True)
        market_type: str = field(default="swap", init= False)
        # Data needed for ranking in ranking.py
        data_source_exchange: str = field(default= (account_file["ranking"]["data_source_exchange"] or "bybit"), repr=False)
        mode: ClassVar[str] = account_file["ranking"]["mode"] 
        url: ClassVar[str] = account_file["ranking"]["url"]
        local_path: ClassVar[str] = account_file["ranking"]["local_path"]

    except FileNotFoundError:
        logging.error("Account.json was not found, please verify that your file is stored as: /directionalscalper/configs/account.json")
        exit()
    except ValueError as e:
        logging.error(f"A value was awaited but was not available, please verify your account.json file.\n{e}")
        exit()

    def __post_init__(self):
        self.find_exchange()
        if self.exchange.get("market_type"):
            self.market_type = self.exchange["market_type"]
            if self.market_type not in AUTHORIZED_MARKET_TYPE:
                logging.error(f"The chosen exchange has an invalid market type, please choose a valid one: {', '.join(i for i in AUTHORIZED_MARKET_TYPE)}.")
                exit()
        self.get_credentials()

    def get_credentials(self) -> None :
        """Create a dictionary with the api key and the api secret."""
        self.credentials: dict[str,str] = {
        key: value
        for key, value in self.exchange.items()
        if key == "api_key" or key == "api_secret"
    }
        if self.credentials.__len__() != 2:
            logging.error(f"There is an error in account.json. Only {self.credentials.__len__()} found, 2 are needed.")
            exit()
        
    def find_exchange(self):
        """Search the exchange that has the same name and account_name as the given data in the creation of ApiConfig."""
        try:
            self.exchange = [
                exchange for exchange in self.account_file["exchanges"] 
                if exchange["name"] == self.exchange_name
                and exchange["account_name"] == self.account_name
            ][0]
        except IndexError:
            logging.error("Could not find the duo exchange_name/account_name. Please verify your account.json or your inputs at restart.")
            exit()