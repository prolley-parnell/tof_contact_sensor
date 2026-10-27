#File to take saved calibration data and plot it per sensor


from tools.calibrate import read_pickle_dict
import matplotlib.pyplot as plt
import numpy as np
# ---------------- Reading Loop ----------------
def main(calibration_file: list[str]):
    dict_names = [['S0-1', 'S0-2', 'S0-3' , 'S0-3' , 'S0-4' , 'S0-5' , 'S0-6' , 'S0-7' , 'S0-8'] , ['S0-9' , 'S0-10', 'S0-11', 'S0-12' , 'S0-13' , 'S0-14' , 'S0-15', 'S0-16'],
                  ['S1-1', 'S1-2', 'S1-3' , 'S1-3' , 'S1-4' , 'S1-5' , 'S1-6' , 'S1-7' , 'S1-8'] , ['S1-9' , 'S1-10', 'S1-11', 'S1-12' , 'S1-13' , 'S1-14' , 'S1-15', 'S1-16']]
    #Set up plot
    fig, axs = plt.subplots(4, 8, figsize=(15, 10))

    #Read from each file
    for file in calibration_file:
        data_dict = read_pickle_dict(file) #Extract the dictionary from the pkl file

        #Increment over the rows of each sensor
        for ax_row, row in zip(axs, dict_names):
            for ax, sensor_id in zip(ax_row, row):
                data = np.array(data_dict[sensor_id])

                ax.scatter(data[:, 0], data[:, 1], label=file, alpha=0.5)
                ax.set_yscale('log')
                ax.set_title(sensor_id)

    fig.legend(labels=[file for file in calibration_file])

    plt.subplots_adjust(left=0.04, right=0.97, top=0.95, bottom=0.05, wspace=0.23, hspace=0.44)


    try:
        plt.show()
    except KeyboardInterrupt:
        print("Program interrupted by user")


if __name__=="__main__":

    # ---------------- Data Parsing ----------------
    sensor_reading = ["data/calibration_samples.pkl", "data/calibration_samples_1.pkl", "data/calibration_samples_2.pkl", "data/calibration_samples_3.pkl"]
    # sensor_reading = ["data/calibration_collate.pkl"]

    main(sensor_reading)
