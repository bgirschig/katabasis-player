import math

def remap_range(val, inMin, inMax, outMin, outMax):
    inRange = inMax-inMin
    outRange = outMax-outMin
    normalized = (val-inMin) / inRange
    return outMin + normalized * outRange

def clamp(val, min_value=0, max_value=1):
    return min(max(val, min_value), max_value)

def seconds_to_string(seconds):
    remainder, hours = math.modf(seconds/60/60)
    remainder, minutes = math.modf(remainder*60)
    seconds = remainder*60

    return f"{int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}"

def lerp(val, target, time):
    return val + (target-val)*time

def vector_lerp(vector_a, vector_b, time):
    output = []
    for idx in range(len(vector_a)):
        output.append(vector_a[idx] + (vector_b[idx]-vector_a[idx]) * time)
    return output