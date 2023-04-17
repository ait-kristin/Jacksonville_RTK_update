import time
import serial
import requests
import multiprocessing

URL = "http://104.154.82.165:30169/rtk/check"

def send_rtk(device_name):
    url = "http://104.154.82.165:30169/gps/update"                     
    com_port = "/dev/ttyACM0"                         # COM port
    baud = 115200                                     # baud rate                              
    ser = serial.Serial(com_port,baud)
    time.sleep(2)                                     # one second delay 
    print("Connected to COM port: " + com_port)   
    sensor_data = []
    while True:
        getData = ser.readline()                       # read incoming Serial string (latitude, longitude, fix status, horizontal accuracy estimate)
        dataString = getData.decode('utf-8')           # decode incoming UTF-8 endoded byte  
        data = dataString[0:][:-2]
        readings = data.split(",")                     # break 
        sensor_data.append(readings)
        try: 
            unc = float(sensor_data[0][3])
        except:
            unc = 10_000
        latlng = {
            "time": time.time(),
            "unitName": device_name,
            "RTK": True,
            "latitude": float(sensor_data[0][0]),
            "longitude": float(sensor_data[0][1]),
            "uncertainty": unc/1000,
        }
        requests.post(url, json=latlng) 

if __name__ == "__main__":
    RTKs = None
    processes = {}
    while True:
        time.sleep(4)
        print("process", processes)
        try:
            results = requests.get(URL)
            temp = results.raise_for_status()
            # print("hi", temp)
            results = results.json()
        except requests.exceptions.ConnectionError:
            print("\n Failed To Connect To Server. \n")
            pass
        print(results)
        RTKs = results.get("RTK devices")
        running = results.get("running")
        if len(RTKs) > 0:
            for device in RTKs:
                if (device not in list(processes.keys())) and running:
                    processes.update({device: multiprocessing.Process(target=send_rtk, args=(device,))})
                    processes.get(device).start()
                elif (device in list(processes.keys())) and (not running):
                    if processes.get(device):
                        processes.get(device).terminate()
                        processes[device] = None
                elif (device in list(processes.keys())) and running and (not processes.get(device)):
                    processes.update({device: multiprocessing.Process(target=send_rtk, args=(device,))})
                    processes.get(device).start()
