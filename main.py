import re
import matplotlib.pyplot as plt
from datetime import datetime

from modules.plot import plot_figure

temp_file = "Motor_Temprature_Log.log"

with open(temp_file, 'r') as file:
    temp_file = file.readlines()

log_raw_data = []
date_set = set()
for line in temp_file:
    date_set.add(datetime.fromisoformat(line[:10]))
    log_raw_data.append({
        "datetime": datetime.fromisoformat(line[:19]),
        "controller_temp": float(re.search(r"控制器温度\[([\d\.]+)°C\]", line).group(1)),
        "mos_temp": float(re.search(r"MOS温度\[([\d\.]+)°C\]", line).group(1)),
        "motor_stator_temp": float(re.search(r"电机定子温度\[([\d\.]+)°C\]", line).group(1)),
    })
date_list = sorted(date_set)
date_str_list = list(map(lambda d: d.strftime("%Y-%m-%d"), date_list))

##### Choose date and time
plot_date = "2023-10-29"
plot_time_from = "18:00"
plot_time_to = "22:00"
plot_dt_from =  datetime.fromisoformat(f"{plot_date} {plot_time_from}")
plot_dt_to =  datetime.fromisoformat(f"{plot_date} {plot_time_to}")
#####


filtered_date = []
for row in log_raw_data:
    if plot_dt_to > row['datetime'] > plot_dt_from:
        filtered_date.append(row)

plot_figure(filtered_date)

print('end')