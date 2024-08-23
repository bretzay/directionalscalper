
import ccxt
from decimal import Decimal
from uuid import uuid4

from utils.utils import createDecimal
from utils.logger import Logger
from api.exchanges.base_exchange import BaseExchange
from api.api_config import ApiConfig


FILENAME: str = __name__.split(".")[-1]
logging = Logger(logger_name= "api_handler_bybit", filename= f"{FILENAME}.log", stream= True,level= "debug")

def verify_ccxt_has(ccxt_function: str):
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
        print(f"Loading exchange {self.exchange} for API data.")
        self.exchange.load_markets()
        print(f"{self.exchange} has loaded successfully.")

    # Account information / Changes
    @verify_ccxt_has("fetchBalance")
    def get_balance(self, quote: str = "USDT") -> Decimal:
        """Get the balance on the account, in the quote currency."""
        # Checks for spot or derivative account
        account_type = ("SPOT" if self.api_config.market_type == "spot"
            else "CONTRACT" if self.api_config.market_type == "swap" 
            else "UNIFIED")

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

        logging.info(f"There was no {quote} found on this account.")
        return None
    
    @verify_ccxt_has("transfer")
    def transfer_funds(self, 
                       coin: str, 
                       amount: float, 
                       from_account: str, 
                       to_account: str, 
                       params={}) -> None:
        # Creates a unique transfer ID
        params["transferId"] = str(uuid4())

        try:
            transfer_response = self.exchange.transfer(coin,
                                          amount,
                                          from_account,
                                          to_account,
                                          params)
            logging.info(f"Funds transfered successfully. Details: {transfer_response}")
        except ccxt.errors.PermissionDenied as e:
            logging.error(f"API key used do not have access to funds transfer. Full error message: \n{e}")
        except Exception as e:
            logging.error(f"Error occured during funds transfer: {e}")
    
    def set_hedge_mode(self,
                       symbol: str) -> None:
        try:
            self.exchange.set_position_mode(hedged=True, symbol=symbol)
        except Exception as e:
            logging.error(f"Unknown error occured in set_position_mode: {e}")
        
    def get_upnl(self) -> str: ...
    def get_latest_trades(self, symbol: str) -> list: ...

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
        
        try:
            response = self.exchange.cancel_all_orders(params = params)
            logging.info(f"Successfully cancelled orders {response}")
        except Exception as e:
            logging.error(f"An error occured while cancelling all orders: {e}")

    @verify_ccxt_has("cancelOrders")
    def cancel_order(self, order_id: str, symbol: str) -> None:
        """Cancel the order specified by its order id and symbol."""
        try: 
            self.exchange.cancel_order(order_id, symbol)
            logging.info(f"Order {order_id} for {symbol} cancelled successfully.")
        except Exception as e:
            logging.error(f"An error occured while cancelling order {order_id} for {symbol}: {e}")

