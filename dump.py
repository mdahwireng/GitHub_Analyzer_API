import pickle
import os

st_dir = "data/api_state/week"
if not os.path.isdir(st_dir):
                os.makedirs(st_dir)

state_dict = {"batch":5, "run_number":1}

with open(st_dir + "/week_state.pk", "wb") as f:
    pickle.dump(state_dict, f)