# Commands for Magnetic Field Meter

from MPprepCommand  import prepCommand as MPprep 

def Identify(ser) -> str:
    ser.write(MPprep("*IDN?"))
    return (ser.readline().decode().strip())

def fieldMeasure(ser) -> float:
    ser.write(MPprep("MEAS:FLUX?"))
    return float(ser.readline().decode().strip())

def getUnits(ser) -> str:
    ser.write(MPprep("UNIT:FLUX?"))
    return (ser.readline().decode().strip())

def setUnits(ser,units) -> str:
    """Set the units that field is measured in.
    must be 'AM','TESL','GAUS' or 'OERS'"""
    ser.write(MPprep("UNIT:FLUX "+units))
    return (ser.readline().decode().strip())