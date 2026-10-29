#File to direct the robot to places precisely to provide calibration distances

import matplotlib.pyplot as plt
import numpy as np
from tools.calibrate import CalibParams
from tools.file_io import read_pickle_dict, write_pickle_dict
from tools.arduino import Arduino

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

def plot_measure(ax, calibration_dict: dict):
    # Extract plottable data
    ax.clear()
    for sensor_id, samples in calibration_dict.items():
        data = np.array(samples)
        ax.scatter(data[:, 0], data[:, 1], label=sensor_id)

    ax.set_yscale('log')
    ax.legend()

def plot_calibration_curve(ax, calib_obj: CalibParams):
    ax.clear()
    y_data = np.array(range(10, 3000))
    dist_dict = calib_obj.count_to_dist_mm(y_data)
    for i, (sensor, x_data) in enumerate(dist_dict.items()):
        # ax.semilogy(x_data, y_data, label=sensor)
        ax.plot(x_data, y_data, label=sensor)


def plot_error_bar(ax: plt.Axes, calib_obj: CalibParams, input_reading: dict, real_distance: int):
    ax.clear()
    dist_dict = calib_obj.count_to_dist_mm(input_reading)
    for i, (sensor_id, dist) in enumerate(dist_dict.items()):
            error = dist - real_distance
            ax.bar(i, error, label=sensor_id)


# ---------------- Calibration Loop ----------------
def main(calibration_measure_file: str="calibration_samples.pkl", calibration_param_file: str="polynomial_args.pkl", baud_rate: int=115200):

    """
        Runs a loop that allows the user to input the distance, and add it to an array of measurements that pair the count to the true distance for each sensor.
        Parameters
        ----------
        calibration_measure_file: `str`
            The relative path to the calibration file (defaults to "calibration_samples.pkl"), string type
            If calibration_file is set to None, the output is shown in the raw count value rather than mm.
        calibration_param_file: `str`
            The relative path to the calibration parameter file (defaults to "polynomial_args.pkl"), string type
        baud_rate: `int`
            The serial port baud rate (defaults to 115200) for the Arduino device


        Keyboard Input
        -----
            int - Any integer value
                This is interpreted as the distance from a flat surface that the measurement has been taken at.

            "q" - Quit
                Close the script without saving.

            "sm" - Save measurements
                Save the count-distance pairs as a dictionary in a ".pkl" file, at the path specified in the main function.

            "rm" - Read measurements
                The dictionary previously saved in the file is loaded into the script.

            "sc" - Save calibration variables
                The parameters used in the calibration curve are saved per sensor. Must have "fit" the curve before saving.

            "rc" - Read calibration variables
                The dictionary previously saved in the file is loaded into the script with the parameters for the function per sensor.

            "d" - Drop the last measurement
                Remove from the array the last distance saved. Helpful if you type the wrong distance in.

            "f" - Fit the curve to the calibration data
                Fit the curve piecewise, logarithmic then linear.
                f(x, a, b, k2, y0, x0) => [a * np.log10(x) + b, k2 * x + y0 - k2 * x0]

            "t" - Zero the sensor
                Sends the command over serial to the Arduino to re-zero the sensors. This happens automatically at start up of the Arduino.
    """

    # Set up Arduino connection
    gripper_controller = Arduino(baud_rate)
    calib_object = CalibParams(calibration_param_file)


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
                write_pickle_dict(calibration_measure_file, calibration_measurements)

            elif dist == "rm":
                print("Reading measurements...")
                calibration_measurements = read_pickle_dict(calibration_measure_file)

            elif dist == "sc":
                print("Saving calibration variables...")
                calib_object.save_calibration_params(None)

            elif dist == "rc":
                print("Reading calibration variables...")
                calibration_params = calib_object.read_calibration_params(None)

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
                        current_count = gripper_controller.read_sensor_count()
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
                    plot_error_bar(err, calib_object, current_count, dist_int)
                    plot_calibration_curve(poly, calib_object)

            plot_measure(cal, calibration_measurements)
            plt.pause(0.01)

    except KeyboardInterrupt:
        print("Program interrupted by user")

    # Cleanup
    gripper_controller.close()


if __name__=="__main__":

    # ---------------- Configuration ----------------
    BAUD_RATE = 115200

    # ---------------- Data Parsing ----------------
    MEASURE_FILE = "./data/calibration_collate.pkl"
    PARAM_FILE = "./config/polynomial_args.pkl"

    main(MEASURE_FILE, PARAM_FILE, BAUD_RATE)

