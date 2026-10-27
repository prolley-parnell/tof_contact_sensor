# tof_contact_sensor
Git repo for using and calibrating the time of flight contact sensor for ant-inspired grippers

## Basic demo

- Set the python environment to ``.venv/bin/python``


### Visualizer
This file shows the output of the sensor in a plot.
If the first argument is `None`, then the visualizer shows the raw count values.

```python
if __name__ == "__main__":
    # ---------------- Configuration ----------------
    BAUD_RATE = 115200

    # ---------------- Data Parsing ----------------
    CALIBRATION_FILE = "config/polynomial_args.pkl"

    main(calibration_file=CALIBRATION_FILE, baud_rate=BAUD_RATE,
         update_interval=50)  # This prints the reading in mm using the calibration parameters
    # main(calibration_file=None, baud_rate=BAUD_RATE, update_interval=50) #This would print the raw count values
```

``$ uv run src/visualizer.py``


### Calibration

``$ uv run src/run_calibration.py``

At the bottom of this file is where the parameters can be set. There must be a path provided for the calibration and measurements.
If the calibration main loop is instructed to `"sm"` or `"sc"` then the measurements in the file will be overwritten.

```python

if __name__=="__main__":

    # ---------------- Configuration ----------------
    BAUD_RATE = 115200

    # ---------------- Data Parsing ----------------
    MEASURE_FILE = "./data/calibration_collate.pkl"
    PARAM_FILE = "./config/polynomial_args.pkl"

    main(MEASURE_FILE, PARAM_FILE, BAUD_RATE)

```

```python

"""
    Options
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
```

