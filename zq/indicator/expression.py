
def Up(data):
    if len(data)>3:
        result= data[-1]>data[-2] and data[-2] <data[-3]
        return result
    else:
        return 0

def Down(data):
    if len(data)>3:
        result= data[-1]<data[-2] and data[-2] >data[-3]
        return result
    else:
        return 0

def Side(data):
    if data[-1]>data[-2]>data[-3]:
        return 1
    elif data[-1]<data[-2]<data[-3]:
        return -1
    else:
        return 0


def Crossover(data1,data2):
    if data1[-1]>data2[-1] and data1[-2]<data2[-2]:
        return 1
    else:
        return 0


def Crossunder(data1,data2):
    if data1[-1]<data2[-1] and data1[-2]>data2[-2]:
        return 1
    else:
        return 0