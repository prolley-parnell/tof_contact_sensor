import traceback
import serial
import serial.tools.list_ports
import numpy as np
from . calibrate import CalibParams #Directs to import the file calibrate from the current directory


class Arduino:
    calibrator = None

    def __init__(self, baud_rate=115200):
        """ Initialise the serial connection with the Arduino """
        port_name = self._find_arduino_port()
        if port_name is None:
            print("Error: Arduino not found. Please check connection.")
            print("Available ports:", [p.device for p in serial.tools.list_ports.comports()])
            exit()

        print(f"Connecting to {port_name}...")
        try:
            self.ser = serial.Serial(port_name, baud_rate, timeout=2)
        except Exception as e:
            print(f"Failed to connect: {e}")
            exit()

    @staticmethod
    def _find_arduino_port():
        """ Lists the available serial ports. Returns None if no available serial ports """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "Arduino" in port.description or "CH340" in port.description or "USB Serial" in port.description:
                return port.device
        return None

    @staticmethod
    def _parse_sensor_read_line(line) -> dict | Exception:
        """ Convert the string returned over serial to a dictionary where each sensor has its own count.
            The format of the message over serial is in chars.
        """

        try:
            decoded = line.decode('utf-8').strip()
            parts = decoded.split('\t')
            distances = {}
            for part in parts:
                if 'S' in part:
                    name = part.split(':')[0]  #Extract just the sensor name : Format: S1-12 (Sensor array 1, sensor 12)
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

            print(f"Parse Error: {traceback.print_tb(e.__traceback__)}")
            raise e

        return {}

    def init_sensor_calibration(self, calibration_file_path: str | None):
        """ Set up the calibration tool class with the calib params found at the file path. The file should be ``.pkl`` """
        #Read the parameters from file to the class
        if calibration_file_path is not None:
            self.calibrator = CalibParams(calibration_file_path)
            self.calibrator.read_calibration_params(calibration_file_path)

    def request_read_sensor(self) -> None | Exception:
        """ Send the 'r' char to the Arduino, prompting it to return the sensor reading count. """
        try:
            self.ser.write(b'r\n')
        except Exception as e:
            print(f"Serial Write Error: {e}")
            raise e

    def tare(self) -> None | Exception:
        """ Send a serial command to the arduino to zero the tof sensors. """
        try:
            self.ser.write(b't\n')
        except Exception as e:
            print(f"Serial Write Error: {e}")
            raise e

    def read_sensor_count(self) -> dict | Exception:
        """ When the serial buffer is available, read the buffer and ASSUME it is for the sensor.
         Dict is empty for the first comm with the sensor. """
        # TODO: This assumption will change if reading any values from the servo motors
        # 2. Read response
        try:
            if self.ser.in_waiting > 0 or self.ser.readable():
                line = self.ser.readline()
                distances_dict = self._parse_sensor_read_line(line)
                return distances_dict
            else:
                raise Exception("Serial is not readable")
        except Exception as e:
            print(f"Serial Read Error: {traceback.print_tb(e.__traceback__)}")
            raise e


    def read_sensor_mm(self) -> dict | None:
        """ Read the buffer as well as performing the conversion to real distance using the sensor calibration params. """
        if self.calibrator is None:
            raise Exception("Calibration parameters not set")
        else:
            try:
                sensor_count = self.read_sensor_count()
                if len(sensor_count) > 0:
                    dist_dict = self.calibrator.count_to_dist_mm(sensor_count)
                    return dist_dict
                else:
                    return None
            except Exception as e:
                print(f"Read Error: {traceback.print_tb(e.__traceback__)}")
                raise e

    def set_servo_position(self, pos: int) -> None:
        try:
            if pos > 9999:
                raise Exception("Position must be made up of less than 4 bytes (4 digits).")
            self.ser.write(b'm:%i\n' % pos)
        except Exception as e:
            print(f"Write Error: {traceback.print_tb(e.__traceback__)}")
            raise e

    def close(self) -> None:
        """ Close the serial connection """
        if self.ser is not None:
            self.ser.close()
