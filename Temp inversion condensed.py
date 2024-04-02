import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from bs4 import BeautifulSoup
import requests
import matplotlib.colors as mcolors
page = requests.get("https://rucsoundings.noaa.gov/get_soundings.cgi?data_source=Op40&latest=latest&start_year=2023&start_month_name=Dec&start_mday=14&start_hour=17&start_min=0&n_hrs=1.0&fcst_len=shortest&airport=72518&text=Ascii&start=latest")
inputdata = BeautifulSoup(page.text, 'html')
data = inputdata.string[408:]
data = data.strip()
data = ' '.join(data.split())
data = data.replace(" ", ",")
rows = data.split(',')
df = pd.DataFrame([rows[i:i+7] for i in range(0, len(rows), 7)], columns=['TYPE', 'PRESSURE', 'HEIGHT', 'TEMP', 'DEWPT', 'WIND DIR', 'WIND SPD'])
df = df.apply(pd.to_numeric, errors='ignore')
df.replace(99999, np.nan, inplace=True)
def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32
def tenthcelsius_to_celsius(tenthcelcius):
    return (tenthcelcius * 1/10)
def meters_to_feet(meters):
    return (meters * 3.28084)
df['TEMP_celsius'] = df['TEMP'].apply(tenthcelsius_to_celsius)
df['TEMP_fahrenheit'] = df['TEMP_celsius'].apply(celsius_to_fahrenheit)
df['HEIGHT_feet'] = df['HEIGHT'].apply(meters_to_feet)
flaglist = []
filtered_values = df[df['HEIGHT'] <= 8000]
max_height_index = filtered_values['HEIGHT'].idxmax()
df['TEMP_CHANGE'] = df['TEMP'].diff() 
for i in range(max_height_index-1):
    temp_change = df.iloc[i+1, 10]
    if temp_change >= 0:
        flaglist.append(1)
    else:
        flaglist.append(0)
start_indices = []
end_indices = []
count = 0
in_sequence = False
for idx, flag in enumerate(flaglist):
    if flag == 1:
        count += 1
        if count == 1 and not in_sequence:
            start_indices.append(idx)
            in_sequence = True
    else:
        if in_sequence:
            end_indices.append(idx - 1)
            count = 0
            in_sequence = False
df.plot(x='TEMP_fahrenheit', y='HEIGHT_feet', kind='line')
plt.xlabel(r'Temp ($^\circ$F)')
plt.ylabel('Height (feet)')
plt.title('Height vs. Temperature of the most recent weather balloon at Albany')
plt.legend(['Temperature at that Height'])
plt.ylim(0,26246.72)
height_range = df[(df['HEIGHT'] >= 0 ) & (df['HEIGHT'] <= 10000)]['HEIGHT']
temps = df.loc[0:max_height_index, 'TEMP_fahrenheit']
tempmin = temps.min()
tempmax = temps.max()
plt.xlim(tempmin-7,tempmax+7)
colors = mcolors.LinearSegmentedColormap.from_list('red_to_yellow', ['red', 'yellow'])
for i in range(len(start_indices)):
    height_bottom = df.iloc[start_indices[i], 2] * 3.28084
    height_top = df.iloc[end_indices[i]+1, 2]* 3.28084
    color_value = start_indices[i] / max_height_index
    xmid = (tempmin+tempmax)/2
    ymid = (height_bottom+height_top)/2
    plt.fill_betweenx([height_bottom, height_top], tempmin-7, tempmax+7, color=colors(color_value), alpha=0.3)
    plt.text(xmid-30, ymid-600, 'Inversion', fontsize=12, color='red', ha='center', va='bottom')
plt.show()
