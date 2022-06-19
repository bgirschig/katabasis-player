import math

def remap_range(val, inMin, inMax, outMin, outMax):
    inRange = inMax-inMin
    outRange = outMax-outMin
    normalized = (val-inMin) / inRange
    return outMin + normalized * outRange

def seconds_to_string(seconds):
    remainder, hours = math.modf(seconds/60/60)
    remainder, minutes = math.modf(remainder*60)
    seconds = remainder*60

    return f"{int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}"