import pickle

# ---------------- Use Calibration Params --------------
def read_pickle_dict(calibration_args_path: str) -> dict | Exception:
    with open(calibration_args_path, "rb") as file:
        try:
            dict_data = pickle.load(file)
            if isinstance(dict_data, dict):
                return dict_data
            else:
                return Exception("Pickle returned something that's not a dictionary")
        except Exception as e:
            print(f"File Read Error: {e}")
            return e

def write_pickle_dict(calibration_args_path: str, dict_params: dict) -> None | Exception:
    with open(calibration_args_path, "wb") as file:
        try:
            pickle.dump(dict_params, file)
        except Exception as e:
            return e