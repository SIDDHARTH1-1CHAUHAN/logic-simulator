from fastapi import FastAPI, WebSocket
import serial
import serial.tools.list_ports
import json
import threading
import time
import os
from fpdf import FPDF

# Check if running on Raspberry Pi
try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False

app = FastAPI()

# Log Directory
LOG_DIR = "experiment_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Raspberry Pi GPIO Setup
if RPI_AVAILABLE:
    GPIO.setmode(GPIO.BCM)
    INPUT_A_PIN = 17
    INPUT_B_PIN = 27
    OUTPUT_PIN = 22
    GPIO.setup(INPUT_A_PIN, GPIO.IN)
    GPIO.setup(INPUT_B_PIN, GPIO.IN)
    GPIO.setup(OUTPUT_PIN, GPIO.OUT)

# Detect Arduino connection
def find_arduino():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Arduino" in port.description:
            return port.device
    return None

arduino_port = find_arduino()
arduino = None

def connect_arduino():
    global arduino, arduino_port
    arduino_port = find_arduino()
    if arduino_port:
        try:
            arduino = serial.Serial(arduino_port, 9600, timeout=1)
            print(f"Connected to Arduino on {arduino_port}")
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            arduino = None
    else:
        print("Arduino not found. Running in manual/Raspberry Pi mode.")

connect_arduino()

# Store circuit states for manual mode
circuit_state = {"gate": "AND", "inputA": 0, "inputB": 0, "output": 0, "mode": "manual"}
clients = []
simulation_history = []

# Function to fetch experiment descriptions
@app.get("/experiment_description/{gate}")
def get_experiment_description(gate: str):
    experiment_descriptions = {
        "AND": "The AND gate outputs HIGH (1) only when both inputs are HIGH. It is used in logical conditions where all inputs must be true to proceed.",
        "OR": "The OR gate outputs HIGH (1) if at least one input is HIGH. It is commonly used in systems where multiple conditions can trigger an event.",
        "XOR": "The XOR (Exclusive OR) gate outputs HIGH (1) when its inputs are different. It is used in error detection and binary addition operations.",
        "NAND": "The NAND gate is the inverse of the AND gate. It outputs LOW (0) only when both inputs are HIGH. It is a universal gate used to create other logic functions.",
        "NOR": "The NOR gate is the inverse of the OR gate. It outputs HIGH (1) only when both inputs are LOW. It is commonly used in memory circuits.",
        "XNOR": "The XNOR gate (Exclusive NOR) outputs HIGH (1) when inputs are the same. It is used in digital comparators and parity checkers.",
        "NOT": "The NOT gate, or inverter, flips the input signal. If the input is HIGH, it outputs LOW, and vice versa. It is a fundamental building block of logic circuits."
    }
    return {"gate": gate, "description": experiment_descriptions.get(gate, "Description not available.")}

# Function to log experiments
def log_experiment(data):
    log_file = os.path.join(LOG_DIR, f"{data['gate']}_log.txt")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    entry = f"{timestamp} - InputA: {data['inputA']}, InputB: {data['inputB']}, Output: {data['output']}\n"
    simulation_history.append(entry)
    with open(log_file, "a") as file:
        file.write(entry)

# Function to broadcast data
def broadcast(message):
    for client in clients:
        try:
            client.send_text(message)
        except:
            clients.remove(client)

print("Backend running...")
