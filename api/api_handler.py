from __future__ import annotations
from pathlib import Path

import sys
# Add the project root to the PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from utils.logger import Logger
from utils.utils import Decimal
from config import Config
from ranking import Ranking_handler
from api.api_config import ApiConfig
from api.exchanges.base_exchange import BaseExchange, initiate_exchange
# TODO: change all get_auto_rotate_symbols() of the old manager.py to the new API_Handler.ranking.rotator_list or something like that when it is done.
# TODO: Change all the min_qty_threshold to max_min_qty to be clearer?


logging = Logger(logger_name= "api_handler", filename= "Api.log", stream= True,level= "debug")

# All this is just for tests purposes
def main():
    config: Config = Config("configs/config.json")
    apiConfig: ApiConfig = ApiConfig("bybit", "test_acc")
    # print(apiConfig)
    ranking_handler: Ranking_handler = Ranking_handler(apiConfig, config)
    exchange: BaseExchange = initiate_exchange(apiConfig)

    print(Decimal("0.052801", 3))
    #print(exchange.get_balance())
    
    # print(exchange)
if __name__ == "__main__":
    main()

    #new_list = []
    #print(new_list)r
    #while True:
    #    try:
    #        if not sorted(new_list) == sorted(ranking_handler.cached_symbol):
    #            print(f"The list {new_list} is different of {ranking_handler.cached_symbol}, changing its value.")
    #            new_list = ranking_handler.cached_symbol.copy()
    #            print(f"List {new_list} updated.")
    #    except KeyboardInterrupt:
    #        print("You stopped the bot")
    #        exit()