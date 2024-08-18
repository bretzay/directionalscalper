import json
import decimal

def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError as e:
        print(f"No such file or directory, please verify your input. {e.filename}")
        exit()

def Decimal(num: float|str, precision: int = 40):
    zero_in_memory = 0
    if float(num) >= 1:
        precision += len(num.split(".")[0])
    else:
        # Temporaly gets rid of the zeroes after the ".". Counts how many there was to return later
        splited_num = num.split(".")
        while splited_num[1][0] == "0":
            splited_num[1] = splited_num[1].removeprefix("0")
            zero_in_memory += 1
        num = "".join(splited_num[0] + "." + splited_num[1])
        
    context = decimal.Context(prec= precision, rounding=decimal.ROUND_HALF_UP)
    num = context.create_decimal(num)
    if not zero_in_memory:
        return num
    #Recover the zeroes by adding them back and rounding if needed
    while zero_in_memory:
        num = decimal_recover_zero(num)
        zero_in_memory -= 1
    return ".".join(num)

def decimal_recover_zero(number: Decimal):
    splited_num = str(number).split(".")
    if splited_num[1][-1] in "56789":
        list1 = list(splited_num[1])
        list1[-2] = str(int(list1[-2]) + 1)
        splited_num[1] = "".join(list1)
    splited_num[1] = splited_num[1].removesuffix(splited_num[1][-1])
    splited_num[1] = "0"+splited_num[1]
    return splited_num


