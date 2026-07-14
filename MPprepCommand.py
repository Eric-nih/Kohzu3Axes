def prepCommand(str):
    """Prepare text to send to List-Magnetik MP-4000 magnetic field meter"""
    output = bytearray(str,"utf-8") # convert to format for serial communication
    output += bytearray('\r\n',"utf-8") # the meter needs both the carriage return and line feed characters
    return output                 