import math
import random

DEG_TO_RAD = math.pi / 180
RAD_TO_DEG = 180 / math.pi

UP = [0, 1, 0]
DOWN = [0, -1, 0]
RIGHT = [1, 0, 0]
FORWARD = [0, 0, 1]
BACK = [0, 0, -1]

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

def rand_range_gauss(min=-1, max=1, spread=0.1) -> float:
    """ Returns a random number with a (roughly) gaussian distribution, guaranteed to be in the given range
    Args:
        min (float)
        max (float)
        spread (float): How likely is it to get values near the bounds of the min/max range
    """

    if math.isnan(min) or math.isnan(max):
        raise Exception("Invalid parameters for rand_range_gauss")
    if max < min:
        raise Exception("Invalid parameters for rand_range_gauss. This would lead to infinite loops")

    mu = (min + max) / 2
    gauss = (max - min) * spread

    val = None
    while val is None or val < min or val > max:
        val = random.gauss(mu, gauss)

    return val
