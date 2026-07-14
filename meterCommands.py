# Commands for Magnetic Field Meter

from MPprepCommand  import prepCommand as MPprep 

def Identify(ser) -> str:
    ser.write(MPprep("*IDN?"))
    return (ser.readline().decode().strip())

def fieldMeasure(ser) -> float:
    ser.write(MPprep("MEAS:FLUX?"))
    return float(ser.readline().decode().strip())