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
        raise NotImplementedError
    def transfer_funds(self, 
                       code: str, 
                       amount: float, 
                       from_account: str, 
                       to_account: str, 
                       params={}) -> None:
        raise NotImplementedError
    def set_hedge_mode(self) -> None: 
        raise NotImplementedError
    def get_upnl(self) -> str: 
        raise NotImplementedError
    def get_latest_trades(self, 
                          symbol: str) -> list: 
        raise NotImplementedError
    # Positions information
    def get_last_active_time(self) : 
        raise NotImplementedError
    def get_symbol_precision(self, 
                             symbol: str) -> int: 
        raise NotImplementedError
    def get_position(self) -> Positions: 
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
        raise NotImplementedError
    def cancel_all_orders(self, 
                          symbol: str = None, 
                          category: str = "linear") -> None: 
        raise NotImplementedError
    # Leverage + Margin
    def get_max_leverage(self, 
                         symbol) -> int: 
        raise NotImplementedError
    def get_leverage_tiers(self, 
                           symbol): 
        raise NotImplementedError
    def set_cross_margin(self, 
                         symbol: str) -> None: 
        raise NotImplementedError
    def set_leverage(self, 
                     symbol) -> None: 
        raise NotImplementedError
    # Probably useless?
    def get_symbol_info(self, 
                        symbol: str) -> dict[str, str|bool|int|float|dict]: 
        raise NotImplementedError
    def get_position_info(self, 
                          symbol: str): 
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