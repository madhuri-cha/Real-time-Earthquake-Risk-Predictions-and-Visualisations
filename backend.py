from fastapi import FastAPI, WebSocket,WebSocketDisconnect
import requests
import pandas as pd
import json
import pickle
import re
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from pydantic import BaseModel
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from fastapi.responses import StreamingResponse


class Period(BaseModel):
    time : int

App = FastAPI()

start_time = ""

final_data = 0
frontend_data =0

App.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change this in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
@App.post("/period/")
async def getPeriod(T :Period ):
    now = datetime.utcnow()
    
    if T.time == 30:
        duration = timedelta(minutes=30)
    elif T.time == 1:
        duration = timedelta(hours=1)
    elif T.time == 3:
        duration = timedelta(hours=3)
    else : 
        duration = timedelta(hours=6)
    print(duration)
    global start_time
    start_time = (now - duration).isoformat()
   

def getApiData():
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}"

    respones = requests.get(url)
    return respones.json()

def generateData():
    responses = getApiData()
    data = {
    "mag" : [],
    "place" : [],
    'felt': [],
    'cdi': [],
    'tsunami': [],
    'sig': [],
    "nst": [],
    "dmin": [],
    "rms": [],
    "gap": [],
    "magType": [],
    "type": [],
    "time" : [],
    "url" : [],
    "details" : [],
    "title" : [],
    "coordinates" : [],
    }

    for i in responses["features"]:
        data["mag"].append(i["properties"]["mag"])
        data["place"].append(i["properties"]["place"]),
        data['felt'].append(i["properties"]["felt"]),
        data['cdi'].append(i["properties"]["cdi"]),
        data['tsunami'].append(i["properties"]["tsunami"]),
        data['sig'].append(i["properties"]["sig"]),
        data["nst"].append(i["properties"]["nst"]),
        data["dmin"].append(i["properties"]["dmin"]),
        data["rms"].append(i["properties"]["rms"]),
        data["gap"].append(i["properties"]["gap"]),
        data["magType"].append(i["properties"]["magType"]),
        data["type"].append(i["properties"]["type"]),
        data["time"].append(i["properties"]["time"]),
        data["url"].append(i["properties"]["url"]),
        data["details"].append(i["properties"]["detail"]),
        data["title"].append(i["properties"]["title"]),
        data["coordinates"].append(i["geometry"]["coordinates"]),

    data_df = pd.DataFrame(data)
    return data_df


def convert_mag(mag, mag_type):
    if mag_type in ['Mw', 'Mww', 'Mwb', 'Mwc', 'Mwr', 'Mwp']:  
        return mag  # Already in Moment Magnitude scale
    elif mag_type in ['Ml', 'Mlg', 'Mlr', 'Ml(texnet)']:  
        return 0.67 * mag + 0.87  # Convert Local Magnitude (Ml) to Mw
    elif mag_type in ['Mb', 'Mb_lg']:  
        return 1.17 * mag - 0.1  # Convert Body-Wave Magnitude (Mb) to Mw
    elif mag_type in ['Md', 'mdl']:  
        return 0.69 * mag + 2.2  # Convert Duration Magnitude (Md) to Mw
    elif mag_type in ['Mc', 'Mh', 'Ma', 'Mlv']:  
        return 0.67 * mag + 0.87  # Approximate conversion (similar to Ml)
    elif mag_type in ['Me']:  
        return 1.5 * mag - 3.0  # Convert Energy Magnitude (Me) to Mw
    elif mag_type in ['mun']:  
        return 0.67 * mag + 1.0  # Approximate conversion for 'mun'
    else:  
        return mag  # Default: keep original value if unknown

def split_place_feature(df):
    """
    Splits the 'place' column into:
    - 'distance_km': Numerical distance from the location.
    - 'direction': Cardinal direction (e.g., N, S, NE, etc.).
    - 'city': Extracted city/place name.
    - 'state': Extracted state name.
    
    Args:
        df (pd.DataFrame): DataFrame containing the 'place' column.
    
    Returns:
        pd.DataFrame: Updated DataFrame with new columns.
    """
    
    # Ensure 'place' column exists
    if 'place' not in df.columns:
        raise ValueError("Column 'place' not found in DataFrame.")

    # Extract distance (numerical)
    df['distance_km'] = df['place'].apply(lambda x: float(re.search(r'(\d+)\s*km', x).group(1)) if re.search(r'(\d+)\s*km', x) else 0)

    # Extract direction (cardinal)
    directions = ['NNE', 'NNW', 'SSE', 'SSW', 'ENE', 'ESE', 'WNW', 'WSW', 'NE', 'NW', 'SE', 'SW', 'N', 'S', 'E', 'W']
    df['direction'] = df['place'].apply(lambda x: next((d for d in directions if d in x), 'Unknown'))

    # Extract location (city + state)
    df['location'] = df['place'].apply(lambda x: re.sub(r'^\d+\s*km\s*[A-Z]*\s*of\s*', '', x).strip())

    # Split city and state safely
    city_list, state_list = [], []

    for loc in df['location']:
        parts = loc.rsplit(',', 1)  # Split only once from the right
        city_list.append(parts[0].strip())  # Always has at least 1 value (city)
        state_list.append(parts[1].strip() if len(parts) > 1 else 'Unknown')  # Assign 'Unknown' if no state exists

    df['city'] = city_list
    df['state'] = state_list

    return df.drop(columns=['location', 'place']) 
def oneType(dataFrame,type):
    types = ['accidental explosion', 'chemical explosion',
       'earthquake', 'experimental explosion', 'explosion', 'ice quake',
       'landslide', 'mine collapse', 'mining explosion', 'not reported',
       'other event', 'quarry', 'quarry blast', 'rockslide', 'sonic boom',
       'volcanic eruption']
    
    for _ in type:
        if _ not in types:
            _ = 'other event'
        for i in types:
            if i == _:
                dataFrame[i] = 1
            else:
                dataFrame[i] = 0 

        return dataFrame.drop("type",axis = 1)
    


def preprocessData(data_df):
    data_df["felt"] = data_df["felt"].fillna(0)
    data_df["cdi"] = data_df["cdi"].fillna(0)
    data_df = data_df.dropna()
    data_to_frontend = data_df[["mag","place",'tsunami',"type","magType","time","url","details","title","coordinates"]]

    data_df = data_df.drop(["time","url","details","title","coordinates"],axis = 1)
    data_df["mag_converted"] = data_df.apply(lambda row : convert_mag(row["mag"],row["magType"]),axis=1)
    data_to_frontend["mag"] = data_df["mag_converted"]

    data_df = data_df.drop("magType",axis=1)
    data_df = data_df.drop("mag",axis=1)
    data_df = split_place_feature(data_df)
    data_df = data_df.reset_index(drop=True)
    data_df = oneType(data_df,data_df["type"])

    with open("state.json","r") as file:
        stateFreq = json.load(file)
    
    data_df["state"] = data_df["state"].map(stateFreq)

    with open("city.json","r") as file:
        cityFreq = json.load(file)

    data_df["city"] = data_df["city"].map(cityFreq)

    scaler = pickle.load(open("scaler.pkl","rb"))

    df_to_scale = data_df[['felt', 'cdi', 'tsunami', 'sig', 'nst', 'dmin', 'rms', 'gap',
       'accidental explosion', 'chemical explosion', 'earthquake',
       'experimental explosion', 'explosion', 'ice quake', 'landslide',
       'mine collapse', 'mining explosion', 'not reported', 'other event',
       'quarry', 'quarry blast', 'rockslide', 'sonic boom',
       'volcanic eruption', 'distance_km', 'city', 'state']]
    
    scaled_df_data = scaler.transform(df_to_scale)
    scaled_df = pd.DataFrame(scaled_df_data,columns=df_to_scale.columns)
    mag = data_df["mag_converted"]

    final_data = pd.concat([scaled_df,mag],axis=1)
    final_data = final_data.dropna()
    data_to_frontend = data_to_frontend.reset_index(drop = True)
    data_to_frontend = data_to_frontend.loc[data_df.index]
    data_to_frontend = data_to_frontend.reset_index(drop = True)


    return final_data, data_to_frontend


def makePrediction():
    data = final_data
    model = pickle.load(open("kmeans.pkl","rb"))
    predictions = model.predict(data)
   
    risk = []
    for i in predictions:
        if i== 0:
            risk.append("Low")
        elif i == 1:
            risk.append("High")
        else:
            risk.append("Medium")
    return risk

    
def getApiDataForFrontend():
    data = {
        "place" : frontend_data["place"].tolist(),
        "magnitude" : frontend_data["mag"].tolist(),
        "time" : frontend_data["time"].tolist(),
        "url" : frontend_data["url"].tolist(),
        "details" : frontend_data["details"].tolist(),
        "type" : frontend_data["type"].tolist(),
        "title" :frontend_data["title"].tolist(),
        "coordinates" : frontend_data["coordinates"].tolist(),
        "tsunami" : frontend_data["tsunami"].tolist(),
        "magType" : frontend_data["magType"].tolist(),
        "predictions" : makePrediction()
    }   
    return data


def generateGraphs(graphType):
    df = pd.DataFrame(getApiDataForFrontend())
    if graphType == "histogram":
        sns.histplot(df["magnitude"], bins=20, kde=True, color="royalblue", alpha=0.6)
        plt.axvline(df["magnitude"].mean(), color='red', linestyle='dashed', linewidth=1, label=f"Mean: {df['magnitude'].mean():.2f}")
        plt.axvline(df["magnitude"].median(), color='green', linestyle='dashed', linewidth=1, label=f"Median: {df['magnitude'].median():.2f}")
        plt.xlabel("Magnitude", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.title("Distribution of Earthquake Magnitudes", fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)

    elif graphType == "pie":
        df_counts = df["predictions"].value_counts()
        plt.pie(df_counts, labels=df_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("pastel"))
        plt.title("Proportion of Risk Levels", fontsize=14, fontweight='bold')
    
    elif graphType == "tsunami":
        tsunami_counts = df["tsunami"].value_counts()
        plt.pie(tsunami_counts, labels=["Yes" if i == 1 else "No" for i in tsunami_counts.index], 
        autopct='%1.1f%%', startangle=140, colors=[ "lightblue","red"])
        plt.title("Presence of Tsunami", fontsize=14, fontweight='bold')
       
    elif graphType == "boxplot":
        sns.boxplot(x=df["magnitude"], color="skyblue", linewidth=1.5, boxprops=dict(facecolor="lightblue"))
        plt.axvline(df["magnitude"].mean(), color='red', linestyle='dashed', linewidth=1, label=f"Mean: {df['magnitude'].mean():.2f}")
        plt.axvline(df["magnitude"].median(), color='green', linestyle='dashed', linewidth=1, label=f"Median: {df['magnitude'].median():.2f}")
        plt.title("Magnitude Boxplot", fontsize=14, fontweight='bold')
        plt.xlabel("Magnitude", fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
    
  

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    return StreamingResponse(buf, media_type="image/png")  

@App.get("/graph/{graph_type}/")
async def sendGraph(graph_type : str):
    return generateGraphs(graph_type)



@App.websocket("/ws")
async def communicate(websocket : WebSocket):
    global final_data, frontend_data
    final_data, frontend_data = preprocessData(generateData())

    await websocket.accept()
    try :
        await websocket.send_json(getApiDataForFrontend())
    except WebSocketDisconnect:
        print("Websocket is disconnected")
      


