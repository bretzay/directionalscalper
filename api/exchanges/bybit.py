
import ccxt
from decimal import Decimal

from utils.utils import createDecimal
from utils.logger import Logger
from api.exchanges.base_exchange import BaseExchange
from api.api_config import ApiConfig


FILENAME: str = __name__.split(".")[-1]
logging = Logger(logger_name= "api_handler_bybit", filename= f"{FILENAME}.log", stream= True,level= "debug")

def verify_ccxt_has(ccxt_function: None):
    """Checks for the selected function name and """
    def decorator(func):
        def wrapper(*args):
            if args[0].exchange.has.get(ccxt_function, None):
                return func(*args)
            logging.error(f"The function {ccxt_function} was not found in CCXT, please verify it.")
            exit()
        return wrapper
    return decorator

class BybitExchange():#BaseExchange):
    def __init__(self, config: ApiConfig):
        #super().__init__()
        self.api_config = config
        self.exchange: ccxt.Exchange = ccxt.bybit({
            "apiKey": self.api_config.credentials["api_key"],
            "secret": self.api_config.credentials["api_secret"]
        })
    
    @verify_ccxt_has("fetchBalance")
    def get_balance(self, quote: str = "USDT") -> Decimal:
        """Get the balance on the account, in the quote currency."""
        # Checks for spot or derivative account
        account_type = "SPOT" if self.api_config.market_type == "spot" else "CONTRACT"

        # Fetch the balance with params to specify the account type if needed
        try:
            balance_response = self.exchange.fetch_balance({"accountType": account_type})
        except ccxt.ExchangeError as e:
            logging.error(f"There was an Exchange error while fetching balance: {str(e)}")

        # Parse the balance
        if quote in balance_response['total']:
            total_balance = createDecimal(str(balance_response['total'][quote]), 2)
            if total_balance > createDecimal(0.00, 2):
                return total_balance

        logging.info(f"There was no USDT found on this account.")
        return None

    @verify_ccxt_has("cancelAllOrders")
    def cancel_all_orders(self, symbol: str = None, category: str = "linear") -> None:
        """
        Cancels all open orders for a specific category. If a symbol is provided, only orders for that symbol are cancelled.

        :param symbol: Optional. The market symbol (e.g., 'BTC/USDT') for which to cancel orders. If None, all orders in the specified category are cancelled.
        :param category: The category of products for which to cancel orders (e.g., 'linear', 'inverse'). Default is 'linear'.
        :return Response: Response from the exchange indicating success or failure.
        """
        params = {"category": category}

        if symbol:
            market: ccxt = self.exchange.market(symbol)
            params["symbol"] = market["id"]

        response = self.exchange.cancel_all_orders(params = params)
        logging.info(f"Successfully cancelled orders {response}")
        

    def cancel_order(self):
        ...