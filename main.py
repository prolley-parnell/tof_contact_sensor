#Function that calibrates the sensor and writes the calibration values to file
import functools
import serial
import serial.tools.list_ports
import pickle
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

# ---------------- Serial Setup ----------------
def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Arduino" in port.description or "CH340" in port.description or "USB Serial" in port.description:
            return port.device
    return None

# ---------------- Data Parsing ----------------
CALIBRATION_FILE = "calibration_samples.pkl"
POLYNOMIAL_FILE = "polynomial_args.pkl"

def parse_arduino_line(line):
    try:
        decoded = line.decode('utf-8').strip()
        parts = decoded.split('\t')
        distances = {}
        for part in parts:
            if 'S' in part:
                name = part.split(':')[0] #Extract just the sensor name : Format: S1-12 (Sensor array 1, sensor 12)
                val_str = part.split(':')[1]
                if val_str.isdigit():
                    try:
                        dist = int(val_str)
                    except ValueError:
                        dist = 0
                else:
                    dist = np.nan
                distances[name] = dist

        if len(distances) == 32:
            return distances
    except Exception as e:
        print(f"Parse Error: {e}")

    return {}

# ---------------- Calibration Plotting ----------------

def fit_curve_to_data(calibration_samples_dict: dict):
    #Each key is the name of the sensor
    #The dict array that follows is the values for the polynomial, highest value first
    polynomial = {}
    for sensor, measurement_list in calibration_samples_dict.items():
        data_array = np.array(measurement_list)
        data_array_without_na = data_array[~np.isnan(data_array[:, 1]), :]

        if len(data_array_without_na) > 4:
            p = np.polyfit(data_array_without_na[0], data_array_without_na[1], 3)
            polynomial[sensor] = p
        else:
            polynomial[sensor] = []

    return polynomial

def plot_error(ax, polynomial_dict:dict, input_reading: dict, real_distance: int):

    ax.clear()
    for i, (sensor_id, p) in enumerate(polynomial_dict.items()):
        if len(p) != 0:
            measured_count = input_reading[sensor_id]
            calculated_dist = np.polyval(p, measured_count)
            error = calculated_dist - real_distance

            ax.bar(i, error, label=sensor_id)


def plot_count(ax, calibration_dict: dict):
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

        ax.semilogy(x_data, y_data, label=sensor_id)


# ---------------- Animation Loop ----------------



def main():
    # ---- Connect over serial ----
    port_name = find_arduino_port()
    if port_name is None:
        print("Error: Arduino not found. Please check connection.")
        print("Available ports:", [p.device for p in serial.tools.list_ports.comports()])
        exit()

    print(f"Connecting to {port_name}...")
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=2)
    except Exception as e:
        print(f"Failed to connect: {e}")
        exit()

    # ---------------- Matplotlib Setup ----------------
    plt.ion()
    fig, (cal, err) = plt.subplots(2, figsize=(14, 9))

    # Create animation (blit=False is required for 3D axis clear/redraw)
    calibration_samples = {}
    polynomial_data = {}

    quit_flag = False

    while not quit_flag:
        # 1. Send command to Arduino
        try:
            ser.write(b'r\n')
        except Exception as e:
            print(f"Serial Write Error: {e}")
            break

        # 2. Read response
        if ser.in_waiting > 0 or ser.readable():
            line = ser.readline()
            distances_dict = parse_arduino_line(line)
            current_heights = np.array(distances_dict.values())


            if not np.all(current_heights) == 0:
                print("It's time to calibrate!")
                dist = input("What distance in mm is the sensor from the surface? ")

                if dist == "q":
                    quit_flag = True
                    ser.close()
                    quit()

                elif dist == "sc":
                    print("Saving calibration...")
                    with open(CALIBRATION_FILE, "wb") as file:
                        try:
                            pickle.dump(calibration_samples, file)
                        except Exception as e:
                            print(f"File Write Error: {e}")

                elif dist == "rc":
                    print("Reading calibration...")
                    with open(CALIBRATION_FILE, "rb") as file:
                        try:
                            calibration_samples = pickle.load(file)
                        except Exception as e:
                            print(f"File Read Error: {e}")

                elif dist == "sp":
                    print("Saving polynomial variables...")
                    with open(POLYNOMIAL_FILE, "wb") as file:
                        try:
                            pickle.dump(polynomial_data, file)
                        except Exception as e:
                            print(f"File Write Error: {e}")

                elif dist == "rp":
                    print("Reading polynomial variables...")
                    with open(POLYNOMIAL_FILE, "rb") as file:
                        try:
                            polynomial_data = pickle.load(file)
                        except Exception as e:
                            print(f"File Read Error: {e}")

                elif dist == "d":
                    print("Dropping the last sample...")
                    for sensor in distances_dict.keys():
                        calibration_samples[sensor].pop()

                elif dist == "f":
                    print("Fit the curve to the calibration data...")
                    if len(calibration_samples.values()) > 4:
                        polynomial_data = fit_curve_to_data(calibration_samples)


                else:
                    if dist.isdigit():
                        dist_int = int(dist)  # Distance in mm as a whole number

                        # Just add the sample to the array
                        for sensor, count in distances_dict.items():
                            if sensor not in calibration_samples:
                                calibration_samples[sensor] = []
                            calibration_samples[sensor].append([dist_int, count])


                    if polynomial_data:
                        plot_error(err, polynomial_data, distances_dict, dist_int)

        plot_count(cal, calibration_samples)
        plt.pause(0.01)


    # Cleanup
    ser.close()

if __name__=="__main__":
    # ---------------- Configuration ----------------
    BAUD_RATE = 115200
    # Interval in milliseconds (100ms = 10 Hz)
    UPDATE_INTERVAL = 100

    main()
