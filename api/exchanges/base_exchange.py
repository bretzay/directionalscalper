from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
from decimal import Decimal, getcontext
from textwrap import dedent

# Implemented exchanges list:
from api.api_config import ApiConfig


@dataclass
class Positions:
    symbol: str
    long: dict[str, int|float] = field(default_factory= {
        "qty": 0.0,
        "price": 0.0,
        "realised": 0,
        "cum_realised": 0,
        "upnl": 0,
        "upnl_pct": 0,
        "liq_price": 0.0,
        "entry_price": 0.0
    })
    short: dict[str, int|float]  = field(default_factory= {
        "qty": 0.0,
        "price": 0.0,
        "realised": 0,
        "cum_realised": 0,
        "upnl": 0,
        "upnl_pct": 0,
        "liq_price": 0.0,
        "entry_price": 0.0
    })

class BaseExchange():
    # Account information / Changes
    def get_balance(self, 
                    quote: str = "USDT") -> Decimal:
        """Get the balance on the account, in the quote currency."""
        raise NotImplementedError

    def transfer_funds(self, 
                       coin: str, 
                       amount: float, 
                       from_account: str, 
                       to_account: str, 
                       params={}) -> None:
        """Creates a transfer ID and make a transfer from one account to the other of the amount of the selected coin."""
        raise NotImplementedError

    def set_hedge_mode(self,
                       symbol: str) -> None:
        """Sets the account to two-way mode (hedge)."""
        raise NotImplementedError

    def get_upnl(self,
                 symbol: str) -> Decimal:
        """
        Gets the unrealized PnL of the selected coin.

        :return Decimal: Number rounded to 2.
        """
        raise NotImplementedError

    def get_latest_trades(self, 
                          symbol: str,
                          since: int = None,
                          limit: int = 100) -> list:
        """
        Fetch recent trades for the given symbol.

        :param str symbol: Fetched symbol.
        :param int since: Maximum fetching time in milliseconds
        :param int limit: Maximum number of trades fetched.
        :return List: Recent trades. 
        """
        raise NotImplementedError


    # Positions information
    def get_symbol_data(self,
                        symbol: str) -> dict:
        """Returns the precision, min_qty and leverage of specified symbol as a dictionnary."""
        raise NotImplementedError

    def get_position_data(self) -> Positions: 
        raise NotImplementedError

    def get_all_positions(self) -> list[Positions]: 
        raise NotImplementedError


    # Order Creation
    def create_entry_order(self) -> None: 
        raise NotImplementedError

    def create_reduce_only_order(self) -> None: 
        raise NotImplementedError

    def create_takeprofit_order(self) -> None: 
        raise NotImplementedError


    # Order Cancelation
    def cancel_order(self, 
                     order_id: str, 
                     symbol: str) -> None:
        """Cancel the order specified by its order id and symbol."""
        raise NotImplementedError

    def cancel_all_orders(self, 
                          symbol: str = None, 
                          category: str = "linear") -> None:
        """
        Cancels all open orders for a specific category. If a symbol is provided, only orders for that symbol are cancelled.

        :param symbol: Specific symbol to cancel, all if default.
        :param category: The category of products for which to cancel orders (e.g., 'linear', 'inverse'). Default is 'linear'.
        """
        raise NotImplementedError


    # Leverage + Margin
    def get_leverage(self, 
                         symbol) -> dict:
        """
        Get leverage information about this symbol in three category.
        ["max"] for max leverage
        ["current"] for current leverage
        ["tiers"] for tiers of leverage
        """
        raise NotImplementedError

    def set_leverage(self, 
                     symbol) -> None:
        """Set the symbol's leverage to max allowed."""
        raise NotImplementedError


    # Probably useless?
    def get_symbol_data(self, 
                        symbol: str) -> dict[str, str|bool|int|float|dict]: 
        raise NotImplementedError

    def get_position_data(self, 
                          symbol: str):
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
        raise NotImplementedError


from api.exchanges import * # Imports exchanges files here to avoid circular import
def initiate_exchange(config: ApiConfig) -> BaseExchange:
    """
    Initiate an exchange subclass from the list available.
    
    Available exchanges: 
        - Bybit
    """
    AVAILABLE_EXCHANGES: list[str] = ["Bybit",]
    match (config.exchange_name.lower()):
        case "bybit":
            return bybit.BybitExchange(config)
        
        case _:
            # Using dedent to keep the indentation clean
            print(dedent(
                f"""\
                This exchange seems to not be implemented: {config.exchange_name.lower()}
                List of available exchanges: {', '.join(AVAILABLE_EXCHANGES)}

                Verify initiate_exchange function if you're a developper.\
                """)
                )
            exit()