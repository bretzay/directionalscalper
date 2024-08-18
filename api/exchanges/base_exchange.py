from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
from decimal import Decimal, getcontext
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

class BaseExchange(ABC):
    # Account information / Changes
    @abstractmethod
    def get_balance(self) -> Decimal: ...
    @abstractmethod
    def transfer_funds(self) -> None: ...
    @abstractmethod
    def set_hedge_mode(self) -> None: ...
    @abstractmethod
    def get_upnl(self) -> str: ...
    @abstractmethod
    def get_latest_trades(self, symbol: str) -> list: ...
    # Positions information
    @abstractmethod
    def get_last_active_time(self) : ...
    @abstractmethod
    def get_symbol_precision(self, symbol: str) -> int: ...
    @abstractmethod
    def get_position(self) -> Positions: ...
    @abstractmethod
    def get_all_positions(self) -> list[Positions]: ...
    # Order Creation
    @abstractmethod
    def create_entry_order(self) -> None: ...
    @abstractmethod
    def create_reduce_only_order(self) -> None: ...
    @abstractmethod
    def create_takeprofit_order(self) -> None: ...
    # Order Cancelation
    @abstractmethod
    def cancel_order(self, id) -> None: ...
    @abstractmethod
    def cancel_all_orders(self) -> None: ...
    # Leverage + Margin
    @abstractmethod
    def get_max_leverage(self, symbol) -> int: ...
    @abstractmethod
    def get_leverage_tiers(self, symbol): ...
    @abstractmethod
    def set_cross_margin(self, symbol: str) -> None: ...
    @abstractmethod
    def set_leverage(self, symbol) -> None: ...
    # Probably useless?
    @abstractmethod
    def get_symbol_info(self, symbol: str) -> dict[str, str|bool|int|float|dict]: ...
    @abstractmethod
    def get_position_info(self, symbol: str): ...