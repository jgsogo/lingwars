
import os
import sys
import json
import numpy as np
from geopy.geocoders import SERVICE_TO_GEOCODER, get_geocoder_for_service

GEOPY_SECRETS = {}


def memoize(function):
    memo = {}
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper
  
  
def get_geocoders_data(location):
    points = []
    for key,value in SERVICE_TO_GEOCODER.items():
        params = GEOPY_SECRETS.get(key, {})
        try:
            geo = value(**params).geocode(location)
            sys.stdout.write(u"\t%20s: %s, %s\n" % (key, geo.latitude, geo.longitude))
            points.append((geo.latitude, geo.longitude))            
        except Exception as e:
            #sys.stdout.write(u"\t%20s: %s\n" % (key, e))
            pass
    return np.array(points)
    
    
@memoize
def locate_station(location):
    points = get_geocoders_data(location)
    #outliers = points[is_outlier(points)]
    #print(outliers)
    if len(points):
        data = points[is_outlier(points) == False]
        mean = np.mean(data, axis=0)
        std_max = max(np.std(data, axis=0))

        latitude = mean[0]
        longitude = mean[1]

        return latitude, longitude, std_max
    return None, None, None
        
        
# Credit: https://stackoverflow.com/questions/22354094/pythonic-way-of-detecting-outliers-in-one-dimensional-observation-data/22357811#22357811
def is_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor.
    """
    if len(points.shape) == 1:
        points = points[:,None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)

    modified_z_score = 0.6745 * diff / med_abs_deviation

    return modified_z_score > thresh
    
    
if __name__ == '__main__':
    # Parse locations and dates from .json files
    directory = os.path.join(os.path.dirname(__file__), 'internacional')
    sys.stdout.write("Directory: {}\n".format(directory))
    
    output = os.path.join(directory, 'time_location.txt')
    with open(output, "w") as output_file:
        output_file.write("#location,date,longitude,latitude,std_max\n")

        for root, subdirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    if os.path.splitext(file_path)[1] == '.json':
                        with open(file_path) as data_file:    
                            data = json.load(data_file)
                            location = data['location']
                            if len(location.strip()):
                                sys.stdout.write(" - {}:\n".format(location))
                                lat, long, std_max = locate_station(location.lower().strip())
                                if long and lat:
                                    sys.stdout.write("   {}; {}".format(long, lat))
                                    date = "{}-{}-{}".format(data['year'], data['month'], data['day'])
                                    output_file.write("{},{},{},{},{}\n".format(location, date, long,lat, std_max))
                                sys.stdout.write("\n")
                except KeyboardInterrupt:
                    sys.stdout.write("> Keyboard interrupt! Exit gracefully.\n")
                    exit(0)
                except Exception as e:
                    sys.stderr.write("\t error {}\n".format(str(e)))
                    
    sys.stdout.write("Done!")
