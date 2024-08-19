import ccxt

from utils.utils import createDecimal
from utils.logger import Logger
from api.exchanges.base_exchange import BaseExchange
from api.api_config import ApiConfig


FILENAME: str = __name__.split(".")[-1]
logging = Logger(logger_name= "api_handler_bybit", filename= f"{FILENAME}.log", stream= True,level= "debug")

class BybitExchange():#BaseExchange):
    def __init__(self, config: ApiConfig):
        #super().__init__()
        self.api_config = config
        self.exchange = ccxt.bybit({
            "apiKey": self.api_config.credentials["api_key"],
            "secret": self.api_config.credentials["api_secret"]
        })
    

    def get_balance(self) -> createDecimal:
        """Get the balance on the account, in the quote currency."""
        # Checks if fetchBalance module exists in CCXT
        if not self.exchange.has['fetchBalance']:
            return None
        
        # Checks for spot or derivative account
        account_type = "SPOT" if self.api_config.market_type == "spot" else "CONTRACT"

        # Fetch the balance with params to specify the account type if needed
        try:
            balance_response = self.exchange.fetch_balance({"accountType": account_type})
        except ccxt.ExchangeError as e:
            logging.error(f"There was an Exchange error while fetching balance: {str(e)}")

        # Parse the balance
        if "USDT" in balance_response['total']:
            total_balance = createDecimal(str(balance_response['total']["USDT"]), 2)
            return total_balance if total_balance > createDecimal(0.00, 2) else None
        
        logging.info(f"There was no USDT found on this account.")
        return None

    def cancel_all_orders(self):
        ...
    
    def cancel_order(self):
        ...