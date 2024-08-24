import datetime
import ccxt
from decimal import Decimal
from uuid import uuid4
from typing import DefaultDict

from utils.rate_limiter import rate_limiter
from utils.utils import createDecimal
from utils.logger import Logger
from api.exchanges.base_exchange import BaseExchange, Positions
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
    @rate_limiter("GET_wallet-balance", 9, 1,  550, 5)
    def get_balance(self, 
                    quote: str = "USDT") -> Decimal:
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
    @rate_limiter("POST_inter-transfer", 54, 60,  550, 5)
    def transfer_funds(self, 
                       coin: str, 
                       amount: float, 
                       from_account: str, 
                       to_account: str, 
                       params={}) -> None:
        """Creates a transfer ID and make a transfer from one account to the other of the amount of the selected coin."""
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

    @verify_ccxt_has("setPositionMode")
    @rate_limiter("POST_inter-transfer", 54, 60,  550, 5)
    def set_hedge_mode(self,
                       symbol: str) -> None:
        """Sets the account to two-way mode (hedge)."""
        try:
            self.exchange.set_position_mode(hedged=True, symbol=symbol)
        except ccxt.errors.NoChange:
            logging.info(f"No changes were made, hedge mode was already active.")
        except Exception as e:
            logging.error(f"Unknown error occured in set_hedge_mode: {e}")

    # TODO: CHECK FOR UPNL IF IT WORKS, I CAN'T AS I CAN'T USE BYBIT
    @verify_ccxt_has("fetchPositions")
    @rate_limiter("GET_position/list", 9, 1,  550, 5)
    def get_upnl(self,
                 symbol: str) -> Decimal:
        """
        Gets the unrealized PnL of the selected coin.

        :return Decimal: Number rounded to 2.
        """
        # Get pos and initialize unrealized pnl
        positions: list = []
        try:
            positions = self.exchange.fetch_positions([symbol])
        except ccxt.errors.BadSymbol as e:
            logging.error(f"The symbol {symbol} seems to not be available on {FILENAME}.")
        unrealized_pnl = {"long": 0.0,
                          "short": 0.0}
        # Loop through symbol's positions
        for position in positions:
            uPnl = (position.get("unrealizedPnl", 0.0) 
                    if position.get("unrealizedPnl", 0.0) 
                    else 0.0)

            side = position.get("side", None)
            if side == "long":
                unrealized_pnl["long"] += uPnl
            elif side == "short":
                unrealized_pnl["short"] += uPnl
        # Make sure rounding is fine
        unrealized_pnl = {key:createDecimal(value, 2)
                          for key,value in unrealized_pnl.items()}
        return unrealized_pnl

    @verify_ccxt_has("fetchTrades")
    def get_latest_trades(self, 
                          symbol: str,
                          since: int = None,
                          limit: int = 100) -> list:
        """
        Fetch recent global trades for the given symbol.

        No rate limit, that is public API.
        :param str symbol: Fetched symbol.
        :param int since: Maximum fetching time in milliseconds
        :param int limit: Maximum number of trades fetched.
        :return List: Recent trades. 
        """
        return self.exchange.fetch_trades(symbol, since, limit)


    # Positions information
    @verify_ccxt_has("fetchPositions")
    @rate_limiter("GET_position/list", 9, 1,  550, 5)
    def get_symbol_data(self,
                        symbol: str) -> dict:
        """Returns the precision, min_qty and leverage of specified symbol as a dictionnary."""
        symbol_data = {
            "precision": 0,
            "min_qty": 0,
            "leverage": 0,
            }

        symbol_info = self.exchange.market(symbol)

        if "info" in symbol_info:
            # Gets the precision as 5 = 0.00001 (4 zero after the dot)
            precision = str(
                1 + symbol_info["precision"]["price"]
                            ).replace("1","0",1)
            precision = len(precision.split(".")[1])
            symbol_data["precision"] = precision
            
            symbol_data["min_qty"] = symbol_info["limits"]["amount"]["min"]

        positions = self.exchange.fetch_positions(symbol)

        for position in positions:
            symbol_data["leverage"] = createDecimal(position["leverage"], 0)

        return symbol_data

    @verify_ccxt_has("fetchPositions")
    @rate_limiter("GET_position/list", 9, 1,  550, 5)
    def get_position_data(self,
                          symbol: str) -> Positions :
        """
        Create position object for the specified symbol.
        
        Position object contains:
        - The symbol's name
        
        Its attributes for each side:
        - Quantity
        - Price
        - Realised gains
        - Cumulated realised gains
        - Unrealised gains
        - Unrealised percent
        - Liquidation price
        - Entry price
        """
        data = []
        try:
            data = self.exchange.fetch_positions(symbol)
        except Exception as e:
            logging.error(f"There was an error in get_position_data: {e}")
        if not len(data) == 2: return
        long = data[0]
        short = data[1]
        return Positions(
            symbol = symbol,
            long = {
                "qty": long["contracts"],
                "price": long["entryPrice"] or 0,
                "realised": createDecimal(long["realizedPnl"] or 0, 2),
                "cum_realised": createDecimal(long["info"]["cumRealisedPnl"], 2),
                "upnl": createDecimal(long["info"]["unrealisedPnl"], 2),
                "upnl_pct": createDecimal(long["percentage"] or 0, 2),
                "liq_price": createDecimal(
                    long["liquidationPrice"] or 0, 
                    max(len(long["liquidationPrice"] or ""), 5)),
                "entry_price": createDecimal(
                    long["entryPrice"] or 0, 
                    max(len(long["entryPrice"] or ""), 5))
                },
            short = {
                "qty": short["contracts"],
                "price": short["entryPrice"] or 0,
                "realised": createDecimal(short["realizedPnl"] or 0, 2),
                "cum_realised": createDecimal(short["info"]["cumRealisedPnl"], 2),
                "upnl": createDecimal(short["info"]["unrealisedPnl"], 2),
                "upnl_pct": createDecimal(short["percentage"] or 0, 2),
                "liq_price": createDecimal(
                    short["liquidationPrice"] or 0, 
                    max(len(short["liquidationPrice"] or ""), 5)),
                "entry_price": createDecimal(
                    short["entryPrice"] or 0,
                    max(len(short["entryPrice"] or ""), 5))
                }
            )

    def get_all_positions(self) -> None: 
        raise NotImplementedError


    @verify_ccxt_has("cancelAllOrders")
    def cancel_all_orders(self, 
                          symbol: str = None, 
                          category: str = "linear") -> None:
        """
        Cancels all open orders for a specific category. If a symbol is provided, only orders for that symbol are cancelled.

        :param symbol: Specific symbol to cancel, all if default.
        :param category: The category of products for which to cancel orders (e.g., 'linear', 'inverse'). Default is 'linear'.
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
    def cancel_order(self, 
                     order_id: str, 
                     symbol: str) -> None:
        """Cancel the order specified by its order id and symbol."""
        try: 
            self.exchange.cancel_order(order_id, symbol)
            logging.info(f"Order {order_id} for {symbol} cancelled successfully.")
        except Exception as e:
            logging.error(f"An error occured while cancelling order {order_id} for {symbol}: {e}")
