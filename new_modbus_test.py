from pymodbus.client import ModbusSerialClient as ModbusClient
import time
import sys
import glob
import csv
import os
import datetime
from datetime import datetime

# Define Modbus register addresses
UPDATE_TIME_REG = 0
CURR_HOUR_REG = 1
CURR_MIN_REG = 2
CURR_DAY_REG = 3
CURR_MONTH_REG = 4
CURR_YEAR_REG = 5
SWEEP_TYPE_REG = 6
NUM_MEASUREMENTS_REG = 7
NUM_ANGLES_REG = 8
NUM_SWEEPS_REG = 9
MEASUREMENTS_READY_REG = 10
SPECIFIC_ANGLES_START_REG = 11
STAGE_MEASUREMENT_REG = 40
SWEEP_RESULTS_START_REG = 41
EEPROM_INITIALIZE_REG = 500
EEPROM_NUM_ANGLES_REG = 501
EEPROM_NUM_MEASUREMENTS_REG = 502
EEPROM_ANGLES_START_REG = 503
COORDINATES_START_REG = 1000

LAST_MEASUREMENT_TYPE = 0

# Initialize Modbus RTU client
client = ModbusClient(port='/dev/ttyUSB0', baudrate=19200, timeout=1)
client.connect()

def write_results(distance, angle=None, stage=None):
    # Create a new file name based on the current date and time (excluding seconds)
    current_time = datetime.now()
    file_name = current_time.strftime('egismos_measurements_%Y%m%d_%H%M.csv')
    
    # Check if the file already exists
    if not os.path.isfile(file_name):
        with open(file_name, 'a') as newfile:
            header = ["TIMESTAMP", "DISTANCE(mm)", "ANGLE(°)", "REAL ANGLE(°)", "STAGE(mm)"]
            logwriter = csv.writer(newfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL,
                                   lineterminator=os.linesep)
            logwriter.writerow(header)
    
    # Write the measurement data to the file
    with open(file_name, 'a') as logfile:
        logwriter = csv.writer(logfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator=os.linesep)
        measurement_timestamp = current_time.strftime('%m-%d-%Y %H:%M')
        row = [measurement_timestamp, distance, angle, stage]
        logwriter.writerow(row)

def update_time():
    # Get current system time
    now = datetime.now()
    
    # Extract hours, minutes, day, month, and year
    hours = now.hour
    minutes = now.minute
    day = now.day
    month = now.month
    year = now.year

    print(f"Updating time to: {hours:02}:{minutes:02} {day:02}/{month:02}/{year:02}")

    # Write the new time to Modbus holding registers
    client.write_register(CURR_HOUR_REG, hours)
    client.write_register(CURR_MIN_REG, minutes)
    client.write_register(CURR_DAY_REG, day)
    client.write_register(CURR_MONTH_REG, month)
    client.write_register(CURR_YEAR_REG, year)

    # Set UPDATE_TIME_REG to 1 to notify the server of the update
    client.write_register(UPDATE_TIME_REG, 1)

    print("Time updated successfully.")

def initiate_general_measurement():
    print("Enter sweep details:")
    num_angles = int(input("Number of angles: "))
    num_measurements = int(input("Number of measurements: "))
    num_sweeps = int(input("Number of sweeps: "))

    # Write the sweep parameters to the corresponding Modbus registers
    client.write_register(NUM_ANGLES_REG, num_angles)
    client.write_register(NUM_MEASUREMENTS_REG, num_measurements)
    client.write_register(NUM_SWEEPS_REG, num_sweeps)

    # Set SWEEP_TYPE_REG to 1 to start the sweep
    client.write_register(SWEEP_TYPE_REG, 1)

    print("General Sweep initiated successfully.")

def initiate_specific_measurement():
    print("Enter sweep details:")
    num_angles = int(input("Number of angles: "))
    num_measurements = int(input("Number of measurements: "))
    num_sweeps = int(input("Number of sweeps: "))
    specific_angles = []
    for i in range(num_angles):
        angle = int(input(f"Enter angle {i+1} (range -50 to 50): "))
        if angle < -50 or angle > 50:
            print("Angle out of range. Please enter an angle between -50 and 50.")
            return
        # Map the angle to the range of an unsigned 16-bit integer
        mapped_angle = angle + 32768
        specific_angles.append(mapped_angle)

    client.write_register(NUM_ANGLES_REG, num_angles)
    client.write_register(NUM_MEASUREMENTS_REG, num_measurements)
    client.write_register(NUM_SWEEPS_REG, num_sweeps)
    client.write_registers(SPECIFIC_ANGLES_START_REG, specific_angles)

    client.write_register(SWEEP_TYPE_REG, 2)

    print("Specific Sweep initiated successfully.")

def eeprom_initialize():
    num_angles = int(input("Enter default number of angles: "))
    num_measurements = int(input("Enter default number of measurements: "))
    default_angles = [int(input(f"Enter default angle {i+1}: ")) for i in range(num_angles)]

    client.write_register(EEPROM_NUM_ANGLES_REG, num_angles)
    client.write_register(EEPROM_NUM_MEASUREMENTS_REG, num_measurements)
    client.write_registers(EEPROM_ANGLES_START_REG, default_angles)
    client.write_register(EEPROM_INITIALIZE_REG, 1)

    print("EEPROM initialized with default values.")

def view_eeprom_values():
    num_angles = client.read_holding_registers(EEPROM_NUM_ANGLES_REG, 1).registers[0]
    num_measurements = client.read_holding_registers(EEPROM_NUM_MEASUREMENTS_REG, 1).registers[0]
    angles = client.read_holding_registers(EEPROM_ANGLES_START_REG, num_angles).registers

    print("EEPROM Values:")
    print(f"Number of Angles: {num_angles}")
    print(f"Number of Measurements: {num_measurements}")
    print(f"Default Angles: {angles}")

def initiate_configured_measurement():
    client.write_register(SWEEP_TYPE_REG, 3)
    print("Configured Sweep initiated successfully.")

def initiate_timed_measurement():

    angles = [angle + 32768 for angle in [-35, -30, -25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35]]
    num_angles = 15
    num_measurements = 30
    num_sweeps = 1

    def write_sweep_parameters():
        print("Writing sweep parameters.")
        client.write_register(NUM_ANGLES_REG, num_angles)
        client.write_register(NUM_MEASUREMENTS_REG, num_measurements)
        client.write_register(NUM_SWEEPS_REG, num_sweeps)
        client.write_registers(SPECIFIC_ANGLES_START_REG, angles)
        client.write_register(SWEEP_TYPE_REG, 2)

    update_time()
    time.sleep(7)
    write_sweep_parameters()
    last_write_time = time.time()

    while True:

        try:
            if client.read_holding_registers(MEASUREMENTS_READY_REG, 1).registers[0] == 0:
                print("Measurements are not ready yet.")
            else:
                print("Measurements ready.")
                num_angles = client.read_holding_registers(NUM_ANGLES_REG, 1).registers[0]
                stage = client.read_holding_registers(STAGE_MEASUREMENT_REG, 1).registers[0] - 32768
                for i in range(num_angles):
                    angle = client.read_holding_registers(SWEEP_RESULTS_START_REG + (i * 2), 1).registers[0] - 32768
                    measurement = client.read_holding_registers(SWEEP_RESULTS_START_REG + (i * 2) + 1, 1).registers[0] - 32768
                    write_results(distance=measurement, angle=angle, stage=stage)
                print("Results written to file.")
                client.write_register(MEASUREMENTS_READY_REG, 0)
        except Exception as e:
            continue

        current_time = time.time()
        if current_time - last_write_time >= 300:  # 300 seconds = 5 minutes
            update_time()
            time.sleep(7)
            write_sweep_parameters()
            last_write_time = current_time

        time.sleep(1)

def main():
    while True:
        global num_angles, num_measurements
        print("\nModbus Control Menu:")
        print("1. Update Date/Time")
        print("2. Initiate General Measurement Sweep")
        print("3. Initiate Specific Measurement Sweep")
        print("4. Initiate Configured Measurement")
        print("5. Initiate Timed Measurement")
        print("6. View results.")
        print("7. Initialize EEPROM Configuration")
        print("8. View EEPROM Configuration")
        print("9. Exit")

        choice = input("Select an option (1-7): ")

        if choice == '1':
            update_time()
        elif choice == '2':
            initiate_general_measurement()
        elif choice == '3':
            initiate_specific_measurement()
        elif choice == '4':
            initiate_configured_measurement()
        elif choice == '5':
            initiate_timed_measurement()
        elif choice == '6':
            if client.read_holding_registers(MEASUREMENTS_READY_REG, 1).registers[0] == 0:
                print("Measurements are not ready yet, or no measurements have been taken.")
                continue
            else:
                num_angles = client.read_holding_registers(NUM_ANGLES_REG, 1).registers[0]
                num_measurements = client.read_holding_registers(NUM_MEASUREMENTS_REG, 1).registers[0]
                stage = client.read_holding_registers(STAGE_MEASUREMENT_REG, 1).registers[0]
                print(f"Stage = {stage}")
                for i in range(num_angles * num_measurements):
                    angle = client.read_holding_registers(SWEEP_RESULTS_START_REG + (i * 2), 1).registers[0]
                    measurement = client.read_holding_registers(SWEEP_RESULTS_START_REG + (i * 2) + 1, 1).registers[0]
                    print(f"Angle = {angle}, Measurement = {measurement}")
        elif choice == '7':
            eeprom_initialize()
        elif choice == '8':
            view_eeprom_values()
        elif choice == '9':
            print("Exiting program.")
            break
        else:
            print("Invalid option. Please select again.")

if __name__ == "__main__":
    try:
        main()
    finally:
        client.close()