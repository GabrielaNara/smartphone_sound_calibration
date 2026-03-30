# smartphone_sound_calibration
This repository provides tools and guidelines for calibrating smartphone-based acoustic measurements using reference sound level meters (SLM).

-----------------------
Dataset Structure 
-----------------------
The dataset consist on examples of real data from the smartphone apps NoiseCapture (.zip format) and OpeNoise (.txt format)
Also, it contain Fixed sensor data obtained though Class 1 SLM Larson Davis.

----------------------------
File Naming Convention 
----------------------------
Files follow the structure: 
	device-measurement_location.extension

Rules:
	"_" separates device and measurement
	"-" separates measurement and location

where: 	
	device is the identifier of the sensor
	measurement relates to all measurements taken by a device in a location
	lcoation is the place where the device took the measurement

Examples:
	LARSON-m1_p1.xlsx

In this example, the mobile sensors took only one measurement in each location, then the identifier device-measurement is the unique ID of a sensor. For instance, the identifier G1-Aluno1_p1.txt and G2-Aluno5_p3.geojson, p1 and p3 are the locations.	

-----------------------------
Fix Sensor Requirements 
-----------------------------
Reference Sound Level Meter (SLM) can be adjusted at your preferable format. The example uses the following:
format: ".xlsx"
sheet: "Time History"

| Column      | Description                 |
| ----------- | --------------------------- |
| Date        | Start date                  |
| Time        | Start time                  |
| LAeq        | Equivalent level per second |
| 1/3 LZF i   | 1/3 octave band values      |
|             | i where i ∈ [16 Hz – 20 kHz]|

--------------------------------
Mobile Sensor Requirements
--------------------------------
The mobile sensors in this Project represent NoiseCapture and OpeNoise apps measurements. Each processed dataset produces:

| Column      | Description                 |
| ----------- | --------------------------- |
| device      | Device identifier           |
| measurement | Measurement ID              |
| x, y, z     | Coordinates                 |
| duration    | Measurement duration        |
| Date        | Start date                  |
| Time        | Start time                  |
| LAeq(1s)    | Equivalent level per second |
| leq_*       | 1/3 octave band values      |