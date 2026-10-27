#Example file to read the sensor values as real distances
# ---------------- Reading Loop ----------------
def main(calibration_file="polynomial_samples.pkl", baud_rate=115200):
    # Set up Arduino connection
    gripper_controller = Arduino(baud_rate)
    gripper_controller.init_sensor_calibration(calibration_file)


    try:
        while True:
            try:
                # 1. Send command to Arduino
                gripper_controller.request_read_sensor()
                # 2. Read response
                dist_mm = gripper_controller.read_sensor_mm()

                print("Distance: ", [f"{name}: {d:.1f}" for name, d in dist_mm.items()])

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
    CALIBRATION_FILE = "../config/polynomial_args.pkl"

    main(CALIBRATION_FILE, BAUD_RATE)
