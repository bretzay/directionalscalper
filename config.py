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
    drawdown_behavior: drawdown_behavior = field(init= False)
    dashboard: Dashboard | None = field(init= False)
    alerts: Alerts | None = field(init= False)

    def __post_init__(self):
        try: 
            self.config = load_json(self.config_path)
            self.test_orders = self.config.get("test_orders_enabled", False)
            self.logger_level = self.config.get("logger_level", "info")
            self.coin_filters = Coin_Filters(self.config["coin_filter"])
            self.risk_management = Risk_Management(self.config["risk_management"])
            self.drawdown_behavior = drawdown_behavior(self.config["drawdown_behavior"])
            _check_for_category(self, "dashboard", Dashboard)
            _check_for_category(self, "alerts", Alerts)
        except KeyError as e:
            print(f"There may be something missing of value {e} in your config.json, please double check your file or use config_updater.py (KeyError)")
            exit()
        #new_dict = {key:value for key,value in self.coin_filters.__dataclass_fields__}
        #print(new_dict)
    def check_none_value(self):
        ...

    def is_category(self, category:str):
        category = category.lower()
        if getattr(self, category, False):
            return True
        return False
    

@dataclass(slots= True)
class Coin_Filters:
    class_dict: dict 
    max_usd_value: int = field(init= False)
    blacklist: list[str] = field(init= False)
    whitelist: list[str] = field(init= False)

    def __post_init__(self):
        self.max_usd_value = self.class_dict.get("max_usd_value",0)
        self.blacklist = self.class_dict.get("blacklist", field(default_factory= list))
        self.whitelist = self.class_dict.get("whitelist", field(default_factory= list))


@dataclass(slots= True)
class Risk_Management:
    class_dict: dict
    upnl_profit_pct: float = field(init=False)
    max_upnl_profit_pct: float = field(init= False)
    trading_allowed: dict = field(default_factory= lambda: {
        'long': bool,
        'short': bool
    })
    gracefull_stop: dict = field(default_factory= lambda: {
        'long': bool,
        'short': bool
    })

@dataclass(slots= True)
class drawdown_behavior:
    class_dict: dict
    grid: Grid = field(init= False)
    stoploss: Stoploss = field(init= False)

    def __post_init__(self):
        self.grid: Grid = Grid(self.class_dict["grid"])
        self.stoploss: Stoploss = Stoploss(self.class_dict["stoploss"])

@dataclass(slots= True)
class Grid:
    class_dict: dict
    additional_entries_on_signal: bool = field(init= False)
    levels: int = field(init= False)
    strength: float = field(init= False)
    min_gridspan: float = field(init= False)
    max_gridspan: float = field(init= False)
    wallet_exposure: dict = field(default_factory= lambda: {
        'long': float,
        'short': float
    })
    autoreduce: Auto_Reduce = field(init= False)
    failsafe: Failsafe = field(init= False)
    

    def __post_init__(self):
        self.autoreduce: Auto_Reduce = self.class_dict["auto_reduce"]
        self.failsafe: Failsafe = Failsafe(self.class_dict["failsafe"])




@dataclass(slots = True)
class Auto_Reduce:
    class_dict: dict
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
    class_dict: dict
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
    class_dict: dict
    enabled: bool = field(init= False)
    start_pct: float = field(init= False)

    def __post_init__(self):
        try:
            self.enabled = self.class_dict.get("enabled", False)
            _check_types(self)
            _is_pct(("start_pct",self.class_dict["start_pct"]))

            if self.enabled:
                self.start_pct = self.class_dict["start_pct"]
        except KeyError as e:
            logging.error(f"The argument {e} was missing in failsafe in your configuration file.")

@dataclass(slots= True)
class Dashboard:
    enabled: bool

@dataclass(slots= True)
class Alerts:
    class_dict: dict
    discord: Discord = field(init= False)
    telegram: Telegram = field(init= False)
    def __post_init__(self):
        ...

@dataclass(slots=True)     
class Discord:
    class_dict: dict
    enabled: bool = field(init= False)
    embedded_messages: bool = field(init= False)
    webhook_url: str = field(init= False)

@dataclass(slots=True) 
class Telegram:
    class_dict: dict
    enabled: bool = field(init= False)
    embedded_messages: bool = field(init= False)
    bot_token: str = field(init= False)
    chat_id: str = field(init= False)

# The bellow list are all the verification functions, make sure to use _check(your_data, [list, of, function, without, parenthesis]) to check the data !
# Example : _check(self.class_dict["strenght"], [is_type], type(float))

def _check_for_category(self, dict_category: str, Object):
    if self.config.get(dict_category):
        class_category = dict_category.lower()
        setattr(self, class_category, Object(self.config[dict_category]))
    else:
        logging.info(f"The bot has been started, but as no instance of {dict_category} was found in the configuration, this function is deactivated.")

def _check_types(self= None):
    for key, value in self.class_dict.items():
        for key_name, value_type in self.__annotations__.items():
            # First basic verifications, if isn't enabled, no need to validate data, so it can be deleted of config.json without impacting the initialization.
            if not key == key_name: continue
            if key == "enabled" and value == False: return
            # 
            value_type = _str_to_type(value_type)
            if type(value) in value_type:
                print(f"{key_name} is of type {type(value)}, which met the requirements of {value_type}.")
                continue
            if value_type == None:
                print(f"{key} was probably a class of parameters?")
                continue
            logging.error(f"There is a type error in your config. {key_name} is of type {type(value)} but It should be {value_type}")
            raise ValueError

def _str_to_type(value_type):
    """
    Specific to type testing, uses the .__annotations__ on the class being tested to get the type hint of each data.
    When the data is received, it is as string, so it checks the value in the str to make it the specific type.
    value_type is then a type float(type, type), why ? Because I can use "type(value) in value_type" to verify if it is exactly a int or a float.
    Explanation of why I do that on : https://stackoverflow.com/questions/37888620/comparing-boolean-and-int-using-isinstance
    """
    value_type = \
    (bool, bool) if value_type == "bool"\
    else (str, str) if value_type == "str"\
    else (int, int) if value_type == "int"\
    else (float, int) if value_type == "float"\
    else (list, list) if value_type == "list"\
    else (dict, dict) if value_type == "dict"\
    else None
    return value_type

def _is_pct(item: tuple):
    """Checks if percent (float) as tuple built like : [0] is the key, [1] is the value"""
    if isinstance(item, float) and (1 > item[0] > 0):
        print("This is between 1 and 0")
        return item
    logging.error(f"The item: {item} should be between 0 and 1.")
    exit()