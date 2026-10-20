#Function that calibrates the sensor and writes the calibration values to file
import matplotlib.pyplot as plt
import pickle
import numpy as np
from scipy.optimize import curve_fit


class CalibParams:
    def __init__(self, calibration_args_path: str):
        self._calibration_path = calibration_args_path
        self._calibration_params = None

    def set_calibration_params(self, calibration_args: dict):
        self._calibration_params = calibration_args

    def get_calibration_params(self, calibration_args_path: str | None) -> dict:
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
                    # distance_dict[sensor_id] = np.polyval(p, measured_count)
                    # distance_dict[sensor_id] = self.func(measured_count, *p)
                    distance_dict[sensor_id] = self.piecewise_linear(measured_count, *p)

        if not distance_dict:
            raise Exception("No calibration parameters")
        else:
            return distance_dict

    @staticmethod
    def curve(x, a, b):
        return a * np.log10(x) + b

    # @staticmethod
    # def piecewise_linear(x, x0, y0, k1, k2):
        # return np.piecewise(x, [x < x0], [lambda x: k1 * x + y0 - k1 * x0, lambda x: k2 * x + y0 - k2 * x0])

    def piecewise_linear(self, x, x0, y0, a, b, k2):
        return np.piecewise(x, [x < x0], [lambda x: self.curve(x, a, b), lambda x: k2 * x + y0 - k2 * x0])


    def fit_curve_to_data(self, calibration_samples_dict: dict):
        # Each key is the name of the sensor
        # The dict array that follows is the values for the polynomial, highest value first

        polynomial = {}
        for sensor, measurement_list in calibration_samples_dict.items():
            data_array = np.array(measurement_list)

            count = data_array[:, 1]
            data_array_without_na = data_array[~np.isnan(count), :]
            true_dist = data_array_without_na[:, 0]
            count = data_array_without_na[:, 1]

            if len(data_array_without_na) > 4:
                # p = np.polyfit(count, true_dist, 1)

                # p0 = [0.1, 0.5, 100]  # this is a mandatory initial guess
                # popt, pcov = curve_fit(self.func, count, true_dist, p0)

                p0 = np.array([1.16559872e+05, -2.10508285e+03, -2.49412807e+01, 9.12007970e+01, -5.59495872e-03], dtype=np.float64)
                popt, pcov = curve_fit(self.piecewise_linear, count, true_dist, p0)
                print(popt)
                # polynomial[sensor] = p
                polynomial[sensor] = popt
            else:
                polynomial[sensor] = []

        return polynomial

# ---------------- Use Calibration Params --------------
def read_pickle_dict(calibration_args_path: str) -> dict | Exception:
    with open(calibration_args_path, "rb") as file:
        try:
            dict_data = pickle.load(file)
            if isinstance(dict_data, dict):
                return dict_data
            else:
                return Exception("Pickle returned something that's not a dictionary")
        except Exception as e:
            print(f"File Read Error: {e}")
            return e

def write_pickle_dict(calibration_args_path: str, dict_params: dict) -> None | Exception:
    with open(calibration_args_path, "wb") as file:
        try:
            pickle.dump(dict_params, file)
        except Exception as e:
            return e





# ---------------- Calibration Plotting ----------------

def plot_line(ax, calibration_dict: dict):
    # Extract plottable data
    ax.clear()
    for sensor_id, samples in calibration_dict.items():
        data = np.array(samples)
        unique, unique_inverse = np.unique(data[:, 0], sorted=True,
                                           return_inverse=True)  # Find the unique distances and identify where there are repetitions

        x_data = unique
        y_data = []
        for index, distance in enumerate(unique):
            all_value = data[unique_inverse == index, 1]
            average = np.median(all_value)
            y_data.append(average)

        # ax.semilogy(x_data, y_data, label=sensor_id)
        ax.plot(x_data, y_data, label=sensor_id)

    ax.legend()

def plot_count(ax, calibration_dict: dict):
    # Extract plottable data
    ax.clear()
    for sensor_id, samples in calibration_dict.items():
        data = np.array(samples)
        # unique, unique_inverse = np.unique(data[:, 0], sorted=True,
        #                                    return_inverse=True)  # Find the unique distances and identify where there are repetitions

        # x_data = unique
        # y_data = []
        # for index, distance in enumerate(unique):
        #     all_value = data[unique_inverse == index, 1]
        #     average = np.median(all_value)
        #     y_data.append(average)

        # ax.semilogy(x_data, y_data, label=sensor_id)
        ax.scatter(data[:, 0], data[:, 1], label=sensor_id)

    ax.set_yscale('log')
    ax.legend()

def plot_polynomial(ax, calib_obj: CalibParams):
    ax.clear()
    y_data = np.array(range(10, 3000))
    dist_dict = calib_obj.count_to_dist_mm(y_data)
    for i, (sensor, x_data) in enumerate(dist_dict.items()):
        # ax.semilogy(x_data, y_data, label=sensor)
        ax.plot(x_data, y_data, label=sensor)


def plot_error(ax: plt.Axes, calib_obj: CalibParams, input_reading: dict, real_distance: int):
    ax.clear()
    dist_dict = calib_obj.count_to_dist_mm(input_reading)
    for i, (sensor_id, dist) in enumerate(dist_dict.items()):
            error = dist - real_distance
            ax.bar(i, error, label=sensor_id)


# ---------------- Calibration Loop ----------------
def main(calibration_file="calibration_samples.pkl", polynomial_file="polynomial_args.pkl", baud_rate=115200):
    # Set up Arduino connection
    gripper_controller = arduino.Arduino(baud_rate)
    calib_object = CalibParams(polynomial_file)


    # ---------------- Matplotlib Setup ----------------
    plt.ion()
    fig, (cal, err, poly) = plt.subplots(3, figsize=(14, 9))

    calibration_measurements = {}
    calibration_params = {}
    current_count = {}

    quit_flag = False
    try:
        while not quit_flag:
            print("It's time to calibrate!")
            dist = input("What distance in mm is the sensor from the surface? ")

            if dist == "q":
                quit_flag = True
                gripper_controller.close()

            elif dist == "sm":
                print("Saving measurements...")
                write_pickle_dict(calibration_file, calibration_measurements)

            elif dist == "rm":
                print("Reading measurements...")
                calibration_measurements = read_pickle_dict(calibration_file)

            elif dist == "sc":
                print("Saving calibration variables...")
                calib_object.save_calibration_params(None)

            elif dist == "rc":
                print("Reading calibration variables...")
                calibration_params = calib_object.get_calibration_params(None)

            elif dist == "d":
                print("Dropping the last sample...")
                if len(current_count) > 0:
                    for sensor in current_count.keys():
                        calibration_measurements[sensor].pop()

            elif dist == "f":
                print("Fit the curve to the calibration data...")
                if len(calibration_measurements.values()) > 4:
                    calibration_params = calib_object.fit_curve_to_data(calibration_measurements)
                    calib_object.set_calibration_params(calibration_params)

            elif dist == "t":
                print("Zeroing the sensor...")
                gripper_controller.tare()

            else:
                if dist.isdigit():
                    dist_int = int(dist)  # Distance in mm as a whole number

                    try:
                        # 1. Send command to Arduino
                        gripper_controller.request_read_sensor()
                        # 2. Read response
                        current_count = gripper_controller._read_sensor_count()
                        print(current_count)

                    except Exception as e:
                        raise e

                    if not np.all(np.array(current_count.values())) == 0:
                        # Just add the sample to the array
                        for sensor, count in current_count.items():
                            if sensor not in calibration_measurements:
                                calibration_measurements[sensor] = []
                            calibration_measurements[sensor].append([dist_int, count])

                if calibration_params:
                    plot_error(err, calib_object, current_count, dist_int)
                    plot_polynomial(poly, calib_object)

            plot_count(cal, calibration_measurements)
            plt.pause(0.01)

    except KeyboardInterrupt:
        print("Program interrupted by user")

    # Cleanup
    gripper_controller.close()

if __name__=="__main__":
    import arduino

    # ---------------- Configuration ----------------
    BAUD_RATE = 115200
    # Interval in milliseconds (100ms = 10 Hz)
    UPDATE_INTERVAL = 100

    # ---------------- Data Parsing ----------------
    CALIBRATION_FILE = "./calibration_samples.pkl"
    POLYNOMIAL_FILE = "./polynomial_args.pkl"

    main(CALIBRATION_FILE, POLYNOMIAL_FILE)
