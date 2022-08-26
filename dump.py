from datetime import datetime
import pickle
import os


current_week = datetime.now().isocalendar()[1]

st_dir = "data/api_state/week"
if not os.path.isdir(st_dir):
                os.makedirs(st_dir)

state_dict = {
                "batch":6, 
                "run_number":1, 
                "base_url":{
                            "dev":"https://dev-cms.10academy.org", 
                            "prod":"https://cms.10academy.org", 
                            "stage":"https://stage-cms.10academy.org"
                            },
                "previously_analyzed_assignments":[],
                "current_week":current_week
            }

with open(st_dir + "/week_state.pk", "wb") as f:
    pickle.dump(state_dict, f)