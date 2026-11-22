# About the project 

For a long time, I was searching for a project that would combine my interdisciplinary skills and interests into something potentially useful, while also posing a challenge and allowing me to broaden my horizons and experience.

That’s how this idea was created — a combination of my love for Arduino and home labbing.


The concept is fairly simple: creating a mini weather station based on Arduino that monitors temperature and humidity in a room. This data is then sent to a backend server and displayed in real time to the end user through a simple web application.

For the backend, I chose Flask — due to my familiarity with Python and my desire to learn something new.

And to make things even more interesting, the entire backend is packaged into a container so it can run independently of the user’s system configuration.

This project is currently in its early development stage.


# Configuration

Copy `Flask/.env.example` to `Flask/.env` and set the serial port of the Arduino board:

```
cd Flask
cp .env.example .env
```

```
ARDUINO_PORT=/dev/ttyUSB0
```

Change it to the port the board is connected to on the host (for example `/dev/ttyACM0`). Docker Compose uses this value both to map the device into the container and to pass it to the application as an environment variable, so no port scanning is performed.

Run the backend with:

```
cd Flask
docker compose up --build
```


# Credits

This project uses the **arduino‑DHT** library by Mark Ruys  
Licensed under the BSD 3‑Clause License  
https://github.com/markruys/arduino-DHT
