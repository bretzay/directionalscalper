from decimal import Decimal

import ccxt

from utils.logger import Logger
from api.exchanges.base_exchange import BaseExchange


FILENAME: str = __name__.split(".")[-1]
logging = Logger(logger_name= "api_handler_bybit", filename= f"{FILENAME}.log", stream= True,level= "debug")

class BybitExchange():
    def __init__(self, config):
        super().__init__()
        self.api_config = config
        #self.exchange = ccxt.bybit()
        #print(self.exchange)
        #exit()
    
    
    def get_balance(self) -> Decimal:
        if self.exchange.has['fetchBalance']:
            try:
                # Fetch the balance with params to specify the account type if needed
                balance_response = self.exchange.fetch_balance({'type': 'swap'})

                # Log the raw response for debugging purposes
                #logging.info(f"Raw balance response from Bybit: {balance_response}")

                # Parse the balance
                if quote in balance_response['total']:
                    total_balance = balance_response['total'][quote]
                    return total_balance
                else:
                    logging.info(f"Balance for {quote} not found in the response.")
            except Exception as e:
                logging.info(f"Error fetching balance from Bybit: {e}")

        return None