from __future__ import annotations
from dataclasses import dataclass,field
from typing import Optional

from utils.utils import load_json
from utils.logger import Logger

logging = Logger(logger_name="Configuration", filename="Configuration.log", stream= True)

# field(init= False) is use in the majority of the init methods of dataclass to allow the use of Slots
# That make it faster to use (It's probably a tenth of a tenth of a second, but Isn't that worth it ? :D)
# variable initialization is made in the __post_init__ method, verification as well ! 

@dataclass(slots= True)
class Config:
    config_path: str = field(repr= False)
    class_dict: dict = field(init= False, repr= False)
    test_orders: bool = field(init= False)
    logger_level: str = field(init= False)
    coin_filters: Coin_Filters = field(init= False)
    risk_management: Risk_Management = field(init= False)
    drawdown_behavior: drawdown_behavior = field(init= False)
    dashboard: Optional[Dashboard] = field(init= False, default= None)
    alerts: Optional[Alerts] = field(init= False, default= None)

    def __post_init__(self):
        try: 
            self.class_dict = load_json(self.config_path)
            self.test_orders = self.class_dict.get("test_orders_enabled", False)
            self.logger_level = self.class_dict.get("logger_level", "info")
            self.coin_filters = Coin_Filters(self.class_dict["coin_filter"])
            self.risk_management = Risk_Management(self.class_dict["risk_management"])
            self.drawdown_behavior = drawdown_behavior(self.class_dict["drawdown_behavior"])
            _create_optional_category(self, "dashboard", Dashboard)
            _create_optional_category(self, "alerts", Alerts)
        except KeyError as e:
            logging.error(f"There may be something missing of value {e} in your config.json, please double check your file or use config_updater.py (KeyError)")
            exit()

@dataclass()
class Coin_Filters:
    class_dict: dict = field(repr= False)
    max_usd_value: int = field(init= False)
    blacklist: list = field(init= False)
    whitelist: list = field(init= False)

    def __post_init__(self):
        try:
            _check_types(self)
            self.max_usd_value = self.class_dict.get("max_usd_value",0)
            self.blacklist = self.class_dict.get("blacklist", field(default_factory= list))
            self.whitelist = self.class_dict.get("whitelist", field(default_factory= list))
        except ValueError:
            logging.error(f"There is a value error in the coin_filter section")
            exit()

@dataclass(slots= True)
class Risk_Management:
    class_dict: dict = field(repr= False)
    upnl_profit_pct: float = field(init=False)
    max_upnl_profit_pct: float = field(init= False)
    trading_allowed: Trading_Allowed | None = field(init = False, default = None)
    gracefull_stop: Gracefull_Stop | None = field(init= False, default = None)
    def __post_init__(self):
        _check_types(self)
        self.upnl_profit_pct = self.class_dict["upnl_profit_pct"]
        self.max_upnl_profit_pct = self.class_dict["max_upnl_profit_pct"]
        self.trading_allowed = Trading_Allowed(self.class_dict["trading_allowed"])
        _create_optional_category(self,"gracefull_stop", Gracefull_Stop)

@dataclass(slots= True)
class Trading_Allowed:
    class_dict: dict = field(repr= False)
    long: bool = field(init= False)
    short: bool = field(init= False)
    def __post_init__(self):
        try:
            _check_types(self)
            self.long = self.class_dict["long"]
            self.short = self.class_dict["short"]
        except ValueError:
            logging.error(f"There is a value error in the trading_allowed section")
            exit()

@dataclass(slots= True)
class Gracefull_Stop:
    class_dict: dict = field(repr= False)
    long: bool = field(init= False)
    short: bool = field(init= False)
    def __post_init__(self):
        try:
            _check_types(self)
            self.long = self.class_dict["long"]
            self.short = self.class_dict["short"]
        except ValueError:
            logging.error(f"There is a value error in the gracefull_stop section")
            exit()

@dataclass(slots= True)
class drawdown_behavior:
    class_dict: dict = field(repr= False)
    grid: Grid | None = field(init= False, default = None)
    stoploss: Stoploss | None = field(init= False, default = None)

    def __post_init__(self):
        _check_types(self)
        _create_optional_category(self,"grid", Grid) 
        _create_optional_category(self,"stoploss", Stoploss)
        
@dataclass(slots= True)
class Grid:
    class_dict: dict = field(repr= False)
    additional_entries_on_signal: bool = field(init= False)
    levels: int = field(init= False)
    strength: float = field(init= False)
    min_gridspan: float = field(init= False)
    max_gridspan: float = field(init= False)
    wallet_exposure: Wallet_Exposure = field(init= False)
    auto_unstuck: Auto_Unstuck | None = field(init= False, default = None)
    failsafe: Failsafe | None = field(init= False, default = None)
    

    def __post_init__(self):
        _check_types(self)
        self.additional_entries_on_signal = self.class_dict["additional_entries_on_signal"]
        self.levels = self.class_dict["levels"]
        self.strength = self.class_dict["strength"]
        self.min_gridspan = self.class_dict["min_gridspan"]
        self.max_gridspan = self.class_dict["max_gridspan"]
        self.wallet_exposure = Wallet_Exposure(self.class_dict["wallet_exposure"])
        _create_optional_category(self,"auto_unstuck", Auto_Unstuck)
        _create_optional_category(self,"failsafe", Failsafe)

@dataclass(slots= True)
class Wallet_Exposure:
    class_dict: dict = field(repr= False)
    long: float = field(init= False)
    short: float = field(init= False)
    def __post_init__(self):
        try:
            _check_types(self)
            self.long = self.class_dict["long"]
            self.short = self.class_dict["short"]
        except ValueError:
            logging.error(f"There is a value error in the wallet_exposure section")
            exit()

@dataclass(slots = True)
class Auto_Unstuck:
    class_dict: dict = field(repr= False)
    entry_during_au: bool = field(init= False)
    pnl_based_au: Pnl_Based_Au | None = field(init= False, default = None)
    margin_based_au: Margin_Based_Au | None = field(init= False, default = None)
    pnl_based_cooldown: Pnl_Based_Cooldown | None = field(init= False, default = None)
    def __post_init__(self):
        try:
            _check_types(self)
            self.entry_during_au = self.class_dict["entry_during_au"]
            _create_optional_category(self,"pnl_based_au", Pnl_Based_Au)
            _create_optional_category(self,"margin_based_au", Margin_Based_Au)
            _create_optional_category(self,"pnl_based_cooldown", Pnl_Based_Cooldown)
        except ValueError:
            logging.error(f"There is a value error in the pnl_based_au section")
            exit()

@dataclass(slots= True)
class Pnl_Based_Au:
    class_dict: dict = field(repr= False)
    enabled: bool = field(init = False)
    upnl_start_pct: float = field(init= False, default = 0)
    
    def __post_init__(self):
        try:
            _check_types(self)
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
            self.upnl_start_pct = self.class_dict["upnl_start_pct"]
            _is_pct(("upnl_start_pct",self.upnl_start_pct))
        except ValueError:
            logging.error(f"There is a value error in the pnl_based_au section")
            exit()

@dataclass(slots= True)
class Margin_Based_Au:
    enabled: bool = field(init = False)
    class_dict: dict = field(repr= False)
    margin_start_pct: float = field(init= False, default= 0)
    
    def __post_init__(self):
        try:
            _check_types(self)
            # If there is a "enabled" in this config part, then add this two lines after _checktypes, then you can do whatever you need in your code to verify it. 
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
            self.margin_start_pct = self.class_dict["margin_start_pct"]
            _is_pct(("margin_start_pct", self.margin_start_pct))
        except ValueError:
            logging.error(f"There is a value error in the margin_based_au section")
            exit()

@dataclass(slots= True)
class Pnl_Based_Cooldown:
    class_dict: dict = field(repr= False)
    enabled: bool = field(init = False)
    upnl_start_pct: float = field(init= False, default= 0)

    def __post_init__(self):
        try:
            _check_types(self)
            # If there is a "enabled" in this config part, then add this two lines after _checktypes, then you can do whatever you need in your code to verify it. 
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
            self.upnl_start_pct = self.class_dict["upnl_start_pct"]
            _is_pct(("upnl_start_pct", self.upnl_start_pct))
        except ValueError:
            logging.error(f"There is a value error in the pnl_based_cooldown section")
            exit()

@dataclass(slots= True)
class Failsafe:
    class_dict: dict = field(repr= False)
    enabled: bool = field(init= False)
    start_pct: float = field(init= False, default=0)

    def __post_init__(self):
        try:
            _check_types(self)
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
            _is_pct(("start_pct", self.class_dict["start_pct"]))
            self.start_pct = self.class_dict["start_pct"]
            print(self.start_pct)
        except ValueError as e:
            logging.error(f"There is a value error in the failsafe section.")
            exit()

@dataclass(slots= True)
class Stoploss:
    class_dict: dict = field(repr= False)
    enabled: bool = field(init= False)
    start_pct: float = field(init= False, default= 0)
    
    def __post_init__(self):
        try:
            _check_types(self)
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
            _is_pct(("start_pct", self.class_dict["start_pct"]))
            self.start_pct = self.class_dict["start_pct"]
        except ValueError:
            logging.error(f"There is a value error in the stoploss section")
            exit()

@dataclass(slots= True)
class Dashboard:
    enabled: bool = field(init= False) 
    class_dict: dict = field(repr= False)
    shared_data_path: str | None = field(init= False, default= None)
    def __post_init__(self):
        try:
            _check_types(self)
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
            self.shared_data_path = self.class_dict["shared_data_path"]
        except ValueError:
            logging.error(f"There is a value error in the dashboard section")
            exit()

@dataclass(slots= True)
class Alerts:
    class_dict: dict = field(repr= False)
    discord: Discord | None = field(init= False, default= None)
    telegram: Telegram | None = field(init= False, default = None)
    def __post_init__(self):
        try:
            _check_types(self)
            _create_optional_category(self, "discord", Discord)
            _create_optional_category(self, "telegram", Telegram)
        except ValueError:
            logging.error(f"There is a value error in the alerts section")
            exit()

@dataclass(slots= True)
class Discord:
    enabled: bool = field(init = False) # for the last example
    class_dict: dict = field(repr= False)
    embedded_messages: bool | None = field(init= False, default = None)
    webhook_url: str | None = field(init= False, default= None)
    def __post_init__(self):
        try:
            _check_types(self)
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
            if not self.class_dict.get("webhook_url").startswith("https://discord.com/api/webhooks/"): 
                raise SyntaxError
            self.embedded_messages = self.class_dict["embedded_messages"]
            self.webhook_url = self.class_dict["webhook_url"]
        except ValueError as e :
            logging.error(f"There is a value error in the discord section")
            exit()
        except SyntaxError:
            logging.error(f"Double check your discord webhook, it seems to be wrong someway.")

@dataclass(slots= True)
class Telegram:
    enabled: bool = field(init = False) # for the last example
    class_dict: dict = field(repr= False)
    embedded_messages: bool | None = field(init= False, default= None)
    bot_token: str | None = field(init= False, default= None)
    chat_id: str | None = field(init= False, default= None)
    def __post_init__(self):
        try:
            _check_types(self)
            # If there is a "enabled" in this config part, then add this two lines after _checktypes, then you can do whatever you need in your code to verify it. 
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
            self.embedded_messages = self.class_dict["embedded_messages"]
            self.bot_token = self.class_dict["bot_token"]
            self.chat_id = self.class_dict["chat_id"]
        except ValueError:
            logging.error(f"There is a value error in the telegram section")
            exit()


@dataclass(slots= True)
class Template:
    enabled: bool = field(init = False) # for the last example
    class_dict: dict = field(repr= False)
    first_param: str | None = field(init= False, default = None) # default = None only for enabled, if not get rid of it !
    second_param: int | None = field(init= False, default = None)
    third_param: bool | None = field(init= False, default = None)
    def __post_init__(self):
        try:
            _check_types(self)
            # If there is a "enabled" in this config part, then add this two lines after _checktypes, then you can do whatever you need in your code to verify it. 
            self.enabled = self.class_dict.get("enabled", False)
            if not self.enabled: return
        except ValueError:
            logging.error(f"There is a value error in the template section")
            exit()

# The bellow list are all the verification functions, make sure to use _check(your_data, [list, of, function, without, parenthesis]) to check the data !
# Example : _check(self.class_dict["strenght"], [is_type], type(float))

def _create_optional_category(self, dict_category: str, Object):
    if self.class_dict.get(dict_category):
        class_category = dict_category.lower()
        setattr(self, class_category, Object(self.class_dict[dict_category]))
    else:
        logging.info(f"The bot has been started, but as no instance of {dict_category} was found in the configuration, this function is deactivated.")

# GLOBAL VERIFICATION
def _check_types(self) -> None:
    for key, value in self.class_dict.items():
        for key_name, value_type in self.__annotations__.items():
            # First basic verifications, if isn't enabled, no need to validate data, so it can be deleted of config.json without impacting the initialization.
            if not key == key_name: continue
            #print(key_name, value_type)
            #print(key, value)
            if key == "enabled" and value == False: return
            value_type = _str_to_type(value_type)
            # Check if value has one value of the tuple value_type.
            # If value_type is a tuple of None, It means that It encountered a class type, so no verification is done. (verification is done inside the class)
            if type(value) in value_type:
                logging.debug(f"{key_name} is of type {type(value)}, which met the requirements of {value_type}.")
                continue
            if None in value_type:
                logging.debug(f"{key} was probably a class type and so was skipped in the type checking function.")
                continue
            logging.error(f"There is a type error in your config. {key_name} is of type {type(value)} but It should be {value_type}")
            raise ValueError

def _str_to_type(value_type: str) -> tuple:
    """
    Specific to type testing, uses the .__annotations__ on the class being tested to get the type hint of each data.
    When the data is received, it is as string, so it checks the value in the str to make it the specific type.
    value_type is then a type float(type, type), why ? Because I can use "type(value) in value_type" to verify if it is exactly a int or a float.
    Explanation of why I do that on : https://stackoverflow.com/questions/37888620/comparing-boolean-and-int-using-isinstance
    """
    new_value_type: tuple = \
    (bool, bool) if value_type == "bool"\
    else (str, str) if value_type == "str"\
    else (int, int) if value_type == "int"\
    else (float, int) if value_type == "float"\
    else (list, list) if value_type == "list"\
    else (dict, dict) if value_type == "dict"\
    else (None, None)
    return new_value_type

# SPECIFIC VERIFICATIONS : 
def _is_pct(item: tuple[str,float]) -> float:
    """Checks if percent (float) as tuple built like : [0] is the key, [1] is the value"""
    if isinstance(item[1], float) and 1 > item[1] > 0:
        return item[1]
    logging.error(f"The item: {item} should be between 0 and 1.")
    raise ValueError
