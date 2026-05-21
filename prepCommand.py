def prepCommand(str):
    output = bytearray(b'\x02') # ASCII STX character. This is needed by the controller
    output += bytearray(str,"utf-8")
    output += bytearray('\r\n',"utf-8") # the controller needs both the carriage return and line feed characters
    return output                 