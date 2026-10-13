#Example file to read the sensor values as real distances
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
# ---------------- Reading Loop ----------------
def main(calibration_file="polynomial_samples.pkl", baud_rate=115200, update_interval = 50):
    # Set up Arduino connection
    gripper_controller = Arduino(baud_rate)
    gripper_controller.init_sensor_calibration(calibration_file)

    # ---------------- Matplotlib Setup ----------------
    fig = plt.figure(figsize=(14, 9))
    ax = fig.add_subplot(111, projection='3d')

    # Coordinates for 16 bars in 2 rows of 8
    x_positions = np.array([0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4, 5, 6, 7])
    y_positions = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1])

    dx = 0.8
    dy = 0.8
    z_pos = np.zeros(16)

    current_heights = np.zeros(16)

    # Initial dummy plot
    ax.bar3d(x_positions, y_positions, z_pos, dx, dy, current_heights, color='cyan', alpha=0.8)
    ax.set_zlim(0, 40)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)



    def update_func(frame):
        try:
            # 1. Send command to Arduino
            gripper_controller.request_read_sensor()
            # 2. Read response
            dist_mm = gripper_controller.read_sensor_mm()

            # Clear previous frame
            ax.clear()

            # Draw Bars
            ax.bar3d(x_positions, y_positions, z_pos, dx, dy, dist_mm.values(), color='cyan', alpha=0.8)

            # --- ADD TEXT LABELS ON TOP OF BARS ---
            for i in range(16):
                x_center = x_positions[i] + dx / 2
                y_center = y_positions[i] + dy / 2
                z_top = current_heights[i]

                # Only show text if height > 0 to avoid clutter at 0
                label = str(int(z_top))

                # Add text
                ax.text(x_center, y_center, z_top, label,
                        color='black', fontsize=9, ha='center', va='bottom', fontweight='bold')

            # Restore Labels and Limits
            ax.set_xlabel('Sensor Index')
            ax.set_ylabel('Row')
            ax.set_zlabel('Distance (mm)')
            ax.set_zlim(0, 65)  # Max limit 40mm

            ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
            ax.set_xticklabels(['1', '2', '3', '4', '5', '6', '7', '8'])
            ax.set_yticks([0.5, 1.5])
            ax.set_yticklabels(['Row 1', 'Row 2'])
            ax.set_title(f"Live Sensor Readings | Max: {np.max(current_heights)} mm")


        except Exception as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("Program interrupted by user")

    # Create animation (blit=False is required for 3D axis clear/redraw)
    ani = FuncAnimation(fig, update_func, interval=update_interval, blit=False, cache_frame_data=False)

    plt.show()

    # Cleanup
    gripper_controller.close()



if __name__=="__main__":
    from tools.arduino import Arduino
    # ---------------- Configuration ----------------
    BAUD_RATE = 115200

    # ---------------- Data Parsing ----------------
    CALIBRATION_FILE = "./polynomial_args.pkl"

    main(CALIBRATION_FILE, BAUD_RATE)