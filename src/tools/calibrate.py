#Function that calibrates the sensor and writes the calibration values to file
import matplotlib.pyplot as plt

from . file_io import read_pickle_dict, write_pickle_dict

import numpy as np
from scipy.optimize import curve_fit


class CalibParams:
    def __init__(self, calibration_args_path: str):
        self._calibration_path = calibration_args_path
        self._calibration_params = None

    def set_calibration_params(self, calibration_args: dict):
        self._calibration_params = calibration_args

    def read_calibration_params(self, calibration_args_path: str | None) -> dict:
        if calibration_args_path is None:
            calibration_args_path = self._calibration_path

        self._calibration_params = read_pickle_dict(calibration_args_path)
        return self._calibration_params

    def save_calibration_params(self, calibration_args_path: str | None):
        if calibration_args_path is None:
            calibration_args_path = self._calibration_path
        write_pickle_dict(calibration_args_path, self._calibration_params)

    def count_to_dist_mm(self, count_measure: dict | np.ndarray) -> dict | Exception:
        # Use the defined method of estimating the relationship between count and distance to convert a measurement to a distance
        distance_dict = {}
        if isinstance(count_measure, dict) and len(count_measure) == 0:
            raise Exception("Error: count_measure dict cannot be empty")

        if self._calibration_params is None: # Then just plot the count
            if isinstance(count_measure, dict):  # Different measure for each sensor
                for sensor_id, count in count_measure.items():
                    if ~np.isnan(count):
                        distance_dict[sensor_id] = count
            elif isinstance(count_measure, np.ndarray):  # Same reading for each sensor
                distance_dict = count_measure #This will throw up an issue, but I don't have the sensor names here to construct a dict
            else:
                raise Exception("Count measure must be a dict or numpy array")
        else:
            for i, (sensor_id, p) in enumerate(self._calibration_params.items()):
                if len(p) != 0:
                    if isinstance(count_measure, dict):  # Different measure for each sensor
                        measured_count = count_measure[sensor_id]
                    elif isinstance(count_measure, np.ndarray):  # Same reading for each sensor
                        measured_count = count_measure
                    else:
                        raise Exception("Count measure must be a dict or numpy array")

                    #If the count is 0, then set that value to NaN because of how this specific sensor works (the distance is infinite)
                    if measured_count == 0:
                        measured_count = np.nan
                    distance_dict[sensor_id] = self.piecewise_linear(measured_count, *p)

        if not distance_dict:
            raise Exception("No calibration parameters")
        else:
            return distance_dict

    @staticmethod
    def curve(x, a, b):
        return a * np.log10(x) + b

    def piecewise_linear(self, x, x0, y0, a, b, k2):
        return np.piecewise(x, [x < x0], [lambda x: self.curve(x, a, b), lambda x: k2 * x + y0 - k2 * x0])


    def fit_curve_to_data(self, calibration_samples_dict: dict):

        polynomial = {}
        for sensor, measurement_list in calibration_samples_dict.items():
            data_array = np.array(measurement_list)

            count = data_array[:, 1]
            data_array_without_na = data_array[~np.isnan(count), :]
            true_dist = data_array_without_na[:, 0]
            count = data_array_without_na[:, 1]

            if len(data_array_without_na) > 4:
                p0 = np.array([1.16559872e+05, -2.10508285e+03, -2.49412807e+01, 9.12007970e+01, -5.59495872e-03], dtype=np.float64)
                popt, pcov = curve_fit(self.piecewise_linear, count, true_dist, p0)
                print("Curve Fit Params are: ", popt)
                polynomial[sensor] = popt
            else:
                polynomial[sensor] = []

        return polynomial
