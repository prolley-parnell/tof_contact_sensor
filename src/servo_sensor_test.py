#Example file to map the sensor values to servo control
import numpy as np
import time
# ---------------- Reading Loop ----------------
def main(calibration_file="polynomial_samples.pkl", baud_rate=115200):
    # Set up Arduino connection
    gripper_controller = Arduino(baud_rate)
    gripper_controller.init_sensor_calibration(calibration_file)

    servo_open = 180
    servo_close = 0
    current_servo_state = 0

    try:
        while True:
            # 1. Send command to Arduino
            gripper_controller.request_read_sensor()
            # 2. Read response
            if gripper_controller.calibrator is not None:
                dist_mm = gripper_controller.read_sensor_mm()
            else:
                dist_mm = gripper_controller.read_sensor_count()

            if dist_mm is not None:

                print("Distance: ", [f"{name}: {d:.1f}" for name, d in dist_mm.items()])

                value_array = np.array([v for v in dist_mm.values()])
                if ~np.all(np.isnan(value_array)):
                    max_measured = int(np.nanmax(value_array))
                else:
                    print("Distance Error")
                    max_measured = servo_open
                print(max_measured)


                current_servo_state = current_servo_state - (np.clip(current_servo_state - max_measured, -60, 60))

            # Find the max distance and map it on to the position from the sensor
            current_servo_state = np.clip(current_servo_state, a_min=servo_close, a_max=servo_open)
            print(f"Current servo state: {current_servo_state}")

            gripper_controller.set_servo_position(current_servo_state)
            time.sleep(1)


    except Exception as e:
        print(f"Error: {e}")

    except KeyboardInterrupt:
        print("Program interrupted by user")

    # Cleanup
    gripper_controller.close()

if __name__=="__main__":
    from tools.arduino import Arduino
    # ---------------- Configuration ----------------
    BAUD_RATE = 115200

    # ---------------- Data Parsing ----------------
    CALIBRATION_FILE = "config/polynomial_args.pkl"

    main(CALIBRATION_FILE, BAUD_RATE)
