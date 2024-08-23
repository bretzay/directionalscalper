from typing import DefaultDict
import time

from utils.logger import Logger

FILENAME: str = __name__.split(".")[-1]
logging = Logger(logger_name= "rate_limiter", filename= f"{FILENAME}.log", stream= True,level= "debug")

_usage: dict[str, list[float]] = {}

def rate_limiter(_type: str,
                 max_calls_single: int,
                 single_period: int = 5,
                 max_call_full: int = 550,
                 full_period: int = 60):
    """
    Limits the number of iteration of a function.

    :params str _type: type of rate limit for the exchange. ()
    :params int max_calls_single: Maximum amount of calls in the period for the specific rate limit type.
    :params int single_period: Time to allow to max_calls_single in seconds.
    :params int max_call_full: Maximum amount of calls for the whole bot for the specific rate limit type.
    :params int full_period: Time to allow for max_call_full in seconds.
    :returns function: Returns the function called if not going above the rate limit.
    """
    def decorator(function):

        def wrapper(*args, **kwargs):
            def is_max_all():
                """
                Checks for the max total rate limit and stops the bot until the cache is completely clean.
                IT SHOULD NEVER HAPPEN, RELOOK AT THE CODE IF IT HAPPENS!!!
                """
                total = 0
                for key in _usage.keys():
                    total += len(_usage[key])
                if total < max_call_full: return True
                cooldown_for_next_rate = timestamps[-1] + full_period - now
                logging.warning(f"Global rate limit reached, waiting {cooldown_for_next_rate:.2f} secondes to clean the cache.")
                time.sleep(cooldown_for_next_rate)
                total = 0
                _usage.clear()
                logging.info("Global cache cleaned")
            
            # Update timestamp
            now = time.time()
            if _type not in _usage:
                _usage[_type] = []
            timestamps = _usage[_type]
            timestamps[:] = [time 
                             for time in timestamps 
                             if now - time < single_period]
            

            if len(timestamps) < max_calls_single and is_max_all():
                timestamps.append(now)
                return function(*args, **kwargs)
            elif len(timestamps) >= max_calls_single:
                cooldown_for_next_rate = timestamps[-1] + single_period - now
                logging.warning(f"{_type} rate reached its limit, waiting to clear the cache: {cooldown_for_next_rate:.2f} seconds.")
                time.sleep(cooldown_for_next_rate)
                _usage[_type].clear()
                logging.info(f"Single cache cleared.")
        return wrapper
    return decorator