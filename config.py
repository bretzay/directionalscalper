from __future__ import annotations
from dataclasses import dataclass,field
from utils.util import load_json
from typing import ClassVar
from utils.logger import Logger

logging = Logger(logger_name="Configuration", filename="Configuration.log", stream= True)

# field(init= False) is use in the majority of the init methods of dataclass to allow the use of Slots that make it faster to use (it's probably a tenth of a tenth of a second, but Isn't that worth it ? :D)
#variable initialization is made in the __post_init__ method, verification as well ! 

@dataclass(slots= True)
class Config:
    config_path: str
    config: dict = field(init= False)
    test_orders: bool = field(init= False)
    logger_level: str = field(init= False)
    coin_filters: Coin_Filters = field(init= False)
    risk_management: Risk_Management = field(init= False)
    drawdownBehaviour: Drawdown_Behaviour = field(init= False)
    dashboard: Dashboard | None = field(init= False)
    alerts: Alerts | None = field(init= False)

    def __post_init__(self):
        self.config = load_json(self.config_path)
        self.test_orders = self.config.get("test_orders_enabled", False)
        self.logger_level = self.config.get("logger_level", "info")
        self.coin_filters = Coin_Filters(self.config["Coin_Filter"])
        self.risk_management = Risk_Management(self.config["Risk_Management"])
        self.drawdownBehaviour = Drawdown_Behaviour(self.config["Drawdown_Behaviour"])
        _check_for_category(self, "Dashboard", Dashboard)
        _check_for_category(self, "Alerts", Alerts)
        
    def is_category(self, category:str):
        category = category.lower()
        if getattr(self, category, False):
            return True
        return False
    

@dataclass(slots= True)
class Coin_Filters:
    coin_filters: dict 
    volume_check: bool = field(init= False)
    min_distance: float = field(init= False)
    min_volume: float = field(init= False)
    max_usd_value: int = field(init= False)
    max_min_qty: float = field(init = False)
    max_abs_funding_rate: float = field(init = False)
    blacklist: list[str] = field(init= False)
    whitelist: list[str] = field(init= False)

    def __post_init__(self):
        self.volume_check = self.coin_filters.get("volume_check", False)
        self.min_distance = self.coin_filters.get("min_distance")
        self.min_volume = self.coin_filters.get("min_volume")
        self.max_usd_value = self.coin_filters.get("max_usd_value")
        self.max_min_qty = self.coin_filters.get("max_min_qty")
        self.max_abs_funding_rate = self.coin_filters.get("max_abs_funding_rate")
        self.blacklist = self.coin_filters.get("blacklist", field(default_factory= list))
        self.whitelist = self.coin_filters.get("whitelist", field(default_factory= list))

@dataclass(slots= True)
class Risk_Management:
    risk_management: dict
    upnl_profit_pct: float = field(init=False)
    max_upnl_profit_pct: float = field(init= False)
    trading_allowed: dict = field(default_factory= lambda: {
        'long': bool,
        'short': bool
    })
    wallet_exposure: dict = field(default_factory= lambda: {
        'long': float,
        'short': float
    })
    gracefull_stop: dict = field(default_factory= lambda: {
        'long': bool,
        'short': bool
    })

@dataclass(slots= True)
class Drawdown_Behaviour:
    drawdown_behaviour: dict
    grid: Grid = field(init= False)
    autoreduce: Auto_Reduce = field(init= False)
    stoploss: Stoploss = field(init= False)
    failsafe: Failsafe = field(init= False)

    def __post_init__(self):
        self.grid: Grid = field(default_factory= lambda: Grid(self.drawdown_behaviour["Grid"]))
        self.autoreduce: Auto_Reduce = field(default_factory= lambda: Auto_Reduce(self.drawdown_behaviour["Auto_Reduce"]))
        self.stoploss: Stoploss = field(default_factory= lambda: Stoploss(self.drawdown_behaviour["StopLoss"]))
        self.failsafe: Failsafe = field(default_factory= lambda: Failsafe(self.drawdown_behaviour["Failsafe"]))

@dataclass(slots= True)
class Grid:
    additional_entries_on_signal: bool = field(init= False)
    levels: int = field(init= False)
    strength: float = field(init= False)
    outer_price_distance: float = field(init= False)
    min_outer_price_distance: float = field(init= False)
    max_outer_price_distance: float = field(init= False)

@dataclass(slots = True)
class Auto_Reduce:
    auto_reduce: dict
    entry_during_au: bool = field(init= False)
    pnl_based_au: dict = field(default_factory= lambda: {
        'enabled': bool,
        'start_pct':float
        })
    margin_based_au: dict = field(default_factory= lambda: {
        'enabled': bool,
        'start_pct': float
    })
    pnl_based_cooldown: dict = field(default_factory= lambda: {
        'enabled': bool,
        'start_pct': float
    })
    
@dataclass(slots= True)
class Stoploss:
    stoploss: dict
    normal_sl: dict = field(default_factory= lambda: {
        'enabled': bool,
        'start_pct': float
    })
    liquidation_sl: dict = field(default_factory= lambda: {
        'enabled': bool,
        'start_pct': float
    }) 

@dataclass(slots= True)
class Failsafe:
    failsafe: dict
    enabled: bool = field(init= False)
    start_pct: float = field(init= False)

@dataclass(slots= True)
class Dashboard:
    enabled: bool

@dataclass(slots= True)
class Alerts:
    alerts: dict
    discord: Discord = field(init= False)
    telegram: Telegram = field(init= False)
    def __post_init__(self):
        ...

@dataclass(slots=True)     
class Discord:
    discord: dict
    enabled: bool = field(init= False)
    embedded_messages: bool = field(init= False)
    webhook_url: str = field(init= False)

@dataclass(slots=True) 
class Telegram:
    telegram: dict
    enabled: bool = field(init= False)
    embedded_messages: bool = field(init= False)
    bot_token: str = field(init= False)
    chat_id: str = field(init= False)

def _check_for_category(self, dict_category: str, Object):
    # Differenciate class_category of dict_category to make it case insensitive, every name in classes's key shall be lower or it will throw random errors.
    if self.config.get(dict_category):
        class_category = dict_category.lower()
        setattr(self, class_category, Object(self.config[dict_category]))
    else:
        logging.info(f"The bot has been started, but as no instance of {dict_category} was found in the configuration, this function is deactivated.")