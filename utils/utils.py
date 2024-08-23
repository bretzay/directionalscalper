import json
def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError as e:
        print(f"No such file or directory, please verify your input. {e.filename}")
        exit()

import decimal
def createDecimal(num: float|str, precision: int = 40, recursion: bool = False) -> decimal.Decimal:
    context = decimal.Context(prec= precision, rounding=decimal.ROUND_HALF_UP)
    zero_in_memory = 0
    num = str(num)
    # Checks if scientific value and changes it to decimal before proceeding
    if "e" in num and recursion == False:
        num = createDecimal(num, recursion=True)
    # Checks if higher than 1 to ignore digits before the dot in the precision calculation
    if float(num) >= 1:
        precision += len(num.split(".")[0])
    if float(num) == 0:
        num = context.create_decimal(num)
        return num
    else:
        # Temporaly gets rid of the zeroes after the ".". Counts how many there was to return later
        splited_num = str(num).split(".")
        while splited_num[1][0] == "0":
            splited_num[1] = splited_num[1].removeprefix("0")
            zero_in_memory += 1
        num = "".join(splited_num[0] + "." + splited_num[1])
        
    #Recover the zeroes by adding them back and rounding if needed
    while zero_in_memory:
        num = _decimal_recover_zero(num, precision)
        num = ".".join(num)
        zero_in_memory -= 1
    num = context.create_decimal(num)
    return num

def _decimal_recover_zero(number: createDecimal, precision: int):
    splited_num = str(number).split(".")
    while len(splited_num[1]) >= precision:
        if splited_num[1][-1] in "56789":
            list1 = list(splited_num[1])
            list1[-2] = str(int(list1[-2]) + 1)
            splited_num[1] = "".join(list1)
        splited_num[1] = splited_num[1].removesuffix(splited_num[1][-1])
    splited_num[1] = "0"+splited_num[1]
    return splited_num
