import argparse

def parse_coord(nmea: float):
    nmea /= 100
    before_comma = int(nmea)

    after_comma = nmea % 1
    after_comma = (after_comma/6)*10

    return before_comma + after_comma

parser = argparse.ArgumentParser()
parser.add_argument("lat", type=float)
parser.add_argument("lon", type=float)
args = parser.parse_args()

print( f"{parse_coord(args.lat)}, {parse_coord(args.lon)}")
