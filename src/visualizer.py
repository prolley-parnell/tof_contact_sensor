#Example file to read the sensor values as real distances using the calibration parameters, or the count value if the calibration parameters are not provided.
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import traceback
from tools.arduino import Arduino

# ---------------- Reading Loop ----------------
def main(calibration_file: str | None ="polynomial_samples.pkl", baud_rate: int=115200, update_interval: int = 50):
    """
        Parameters
        ----------
        calibration_file: `str`
            The relative path to the calibration file (defaults to "polynomial_samples.pkl"), string type
            If calibration_file is set to None, the output is shown in the raw count value rather than mm.
        baud_rate: `int`
            The serial port baud rate (defaults to 115200) for the Arduino device
        update_interval: `int`
            Delay between frames in milliseconds for plotting (defaults to 50 ms), the call to the arduino is also at this rate.
    """
    # Set up Arduino connection
    gripper_controller = Arduino(baud_rate)
    gripper_controller.init_sensor_calibration(calibration_file)
    if gripper_controller.calibrator is None:
        units = "count"
    else:
        units = "mm"

    # ---------------- Matplotlib Setup ----------------

    fig, (ax1, ax2) = plt.subplots(2, figsize=(14, 9), subplot_kw={'projection': "3d"})

    # Coordinates for 16 bars in 2 rows of 8
    x_positions = np.array([0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7])
    y_positions = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1])

    dx = 0.8
    dy = 0.8
    z_pos = np.zeros(16)

    current_heights = np.zeros(16)

    # Initial dummy plot
    ax1.bar3d(x_positions, y_positions, z_pos, dx, dy, current_heights, color='cyan', alpha=0.8)
    ax1.set_zlim(-1, 60)
    ax2.bar3d(x_positions, y_positions, z_pos, dx, dy, current_heights, color='cyan', alpha=0.8)
    ax2.set_zlim(-1, 60)

    # plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)


    def update_func(frame):
        try:
            # 1. Send command to Arduino
            gripper_controller.request_read_sensor()
            # 2. Read response
            if gripper_controller.calibrator is not None:
                dist_mm = gripper_controller.read_sensor_mm()
            else:
                dist_mm = gripper_controller.read_sensor_count()

            # Clear previous frame
            ax1.clear()
            ax2.clear()

            if dist_mm is not None:

                # --- ADD TEXT LABELS ON TOP OF BARS ---
                for side, ax in zip(["S0", "S1"], [ax1, ax2]):
                    labels = [side + "-" + str(i+1) for i in range(16)]
                    current_heights = [dist_mm[l] if l in dist_mm.keys() else -1 for l in labels]
                    # Draw Bars
                    ax.bar3d(x_positions, y_positions, z_pos, dx, dy, current_heights, color='cyan', alpha=0.8)
                    #Set the labels
                    for i in range(16):
                        x_center = x_positions[i] + dx / 2
                        y_center = y_positions[i] + dy / 2
                        z_top = current_heights[i]


                        if ~np.isnan(z_top):
                            # Only show text if height < 80 to avoid clutter in the other plots
                            if z_top < 80:
                                sensor_measure_label = str(int(z_top))
                            else:
                                sensor_measure_label = ""
                        else:
                            sensor_measure_label = "NaN"

                        # Add text
                        ax.text(x_center, y_center, z_top, sensor_measure_label,
                                color='black', fontsize=9, ha='center', va='bottom', fontweight='bold')

                    # Restore Labels and Limits
                    ax.set_xlabel('Sensor Index')
                    ax.set_ylabel('Row')
                    ax.set_zlabel('Distance (mm)')
                    ax.set_zlim(0, 65)  # Max limit 65mm

                    ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
                    ax.set_xticklabels(['1', '2', '3', '4', '5', '6', '7', '8'])
                    ax.set_yticks([0.5, 1.5])
                    ax.set_yticklabels(['Row 1', 'Row 2'])
                    if ~np.all(np.isnan(current_heights)):
                        ax.set_title(f"Live Sensor Readings | Max: {np.nanmax(current_heights)} {units}")
                    else:
                        ax.set_title(f"Live Sensor Readings | Max: NaN {units}")


        except Exception as e:
            print(f"Error: {e}. {traceback.print_tb(e.__traceback__)}")
        except KeyboardInterrupt:
            print("Program interrupted by user")

    # Create animation (blit=False is required for 3D axis clear/redraw)
    ani = FuncAnimation(fig, update_func, interval=update_interval, blit=False, cache_frame_data=False)

    plt.show()

    # Cleanup
    gripper_controller.close()


if __name__=="__main__":
    # ---------------- Configuration ----------------
    BAUD_RATE = 115200

    # ---------------- Data Parsing ----------------
    CALIBRATION_FILE = "polynomial_args.pkl"

    main(calibration_file=CALIBRATION_FILE, baud_rate=BAUD_RATE, update_interval=50) #This prints the reading in mm using the calibration parameters
    # main(calibration_file=None, baud_rate=BAUD_RATE, update_interval=50) #This would print the raw count values