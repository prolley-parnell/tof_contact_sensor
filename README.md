# tof_contact_sensor
Git repo for using and calibrating the time of flight contact sensor for ant-inspired grippers

## Basic demo

- Set the python environment to ``.venv/bin/python``


### Visualizer
This file shows the output of the sensor in a plot.
If the first argument is `None`, then the visualizer shows the raw count values.

```python
if __name__=="__main__":
    # ---------------- Configuration ----------------
    BAUD_RATE = 115200

    # ---------------- Data Parsing ----------------
    CALIBRATION_FILE = "polynomial_args.pkl"

    main(calibration_file=CALIBRATION_FILE, baud_rate=BAUD_RATE, update_interval=50) #This prints the reading in mm using the calibration parameters
    # main(calibration_file=None, baud_rate=BAUD_RATE, update_interval=50) #This would print the raw count values
```

``$ uv run src/visualizer.py``


### Calibration



