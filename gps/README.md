# 📍 Termux GPS + Live Location Demo

This repo shows how to fetch **live GPS location data** from an Android device using **Termux** and display it with a Python demo script.

---

## ⚡ Steps I Followed

### 1. Install IPWebcam APK Mod on your android

* Download IPWebcam APK Mod 2019-2020 version : [IPWebcam](https://www.apkmirror.com/apk/thyoni-tech/ip-webcam/ip-webcam-1-14-31-737-aarch64-release/)
* Enable GPS settings inside the app. Video Preferences > Enable GPS on start. Optional Permissions > Allow GPS.
* Enable Data Logging.

---

### 2. Install Termux & Termux\:API on your android

* Download [F-Droid](https://f-droid.org) .
* Download **Termux** and **Termux\:API** from F-Droid.
* Enable location permissions to **Termux-API**
* Install both APKs on phone.

---

### 3. Run Test Script

Clone this repo → replace the ip information in the code with your IPWebcam ip address , start the IPWebcam server and run the Python demo:

```bash
python test.py
```

### 4. Set up Termux Environment

Inside **Termux**, run:

```bash
pkg update && pkg upgrade
```
click Y to continue
```
pkg install python
pkg install termux-api
termux-setup-storage
while true
do
  termux-location --request once | \
  curl -X POST -H "Content-Type: application/json" \
  -d @- http://<laptop-ip>:5000/update_location
  sleep 2
done


```

---
for finding your laptop-ip , open cmd in windows and type ipconfig, the IPV4 address is your required laptop-ip


termux-location --request once is used for medium to high accuracy and when indoors , if that fails , replace it with the following:

1. this command needs outdoor skyview.
```
termux-location -p gps
```
2. this command can work inside a room but might give a 200-400 km difference as it works on ISP registered location
```
termux-location -p network
```


➡️ The video output will start displaying the latitude and longitude.

---



## ⚠️ Notes

* Location accuracy depends on **GPS signal**, sometimes indoor readings can be \~100–400 km off.
* Best results → go outdoors or near a window.
