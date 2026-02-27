"""
- Get data from 1 or more IMUs
- Save Quaternions in a JSON file with timestamp
- Save

"""
import os
os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'

import time
import traceback

import utils.file_operations as file_operations
import utils.serial_operations as serial_op

RED = "\033[1;31m"
RESET = "\033[0;0m"

# logical ids of the IMUs used
imu_ids = [4, 9, 10]


# Standard Labels:
# Torso:     torso_imu, 
# Pelvis:    pelvis_imu, 
# Femur:     femur_r_imu (right) or femur_l_imu (left), 
# Tibia:     tibia_r_imu (right) or tibia_l_imu (left), 
# Calcaneus: calcn_r_imu (right) or calcn_l_imu (left)
imu_labels = ["femur_r_imu", "tibia_r_imu", "femur_l_imu"] # must match order from imu_ids

# name of the JSON file to save the data
file_name = "teste/teste5"

# Set parameters that will be configured
imu_configuration = {
    "disableCompass": True,
    "disableGyro": False,
    "disableAccelerometer": False,
    "gyroAutoCalib": True,
    "filterMode": 1, # kalman filter
    "axisDirections": 5, # X:Forward, Y:Up, Z:Right -> OpenSim Standard
    "tareSensor": True,
    "logical_ids": imu_ids,
    ## 0 - quaternions, 255 - null
    "streaming_commands": [0, 255, 255, 255, 255, 255, 255, 255]
}

# Initialize imu's quaternions
quaternions = {}

for i in range(len(imu_labels)):
    quaternions[imu_labels[i]] = [0, 0, 0, 0]


#  Main function
if __name__ == '__main__':
    # Starts dongle object
    serial_port = serial_op.initialize_imu(imu_configuration)

    # Wait configurations processing to avoid breaking
    time.sleep(2)
    # Wait for user input to start recording
    input("Pressione 'Enter' para iniciar coleta.")
    print("Coleta iniciada!")

    startTime = time.time()
    while True:
        try:
            bytes_to_read = serial_port.inWaiting()

            # If there are data waiting in dongle, process it
            if  0 < bytes_to_read:

                # Obtain data in dongle serial port
                data = serial_port.read(bytes_to_read)

                # Check if data package is OK - See sensor user's manual.
                if data[0] != 0 and len(data)<=3:
                    print(RED, 'Corrupted data read.', RESET)
                    continue

                # extract quaternion data from the first IMU
                for i in range(len(imu_ids)):
                    if data[1] == imu_ids[i]:
                        extracted_data = serial_op.extract_quaternions(data)
                        quaternions[imu_labels[i]] = extracted_data['quaternions']

                # initialize data dictionary
                data_imus = {"time": time.time() - startTime}
                # save quaternion values
                for imu_label in imu_labels:
                    data_imus[imu_label] = str(quaternions[imu_label])

                file_path = file_name + '.json'
                file_operations.write_to_json_file(file_path, data_imus, write_mode='a')

        # finish program execution
        except KeyboardInterrupt:
            print("Finished execution with control + c. ")
            serial_op.stop_streaming(serial_port, imu_configuration['logical_ids'])
            serial_op.manual_flush(serial_port)
            # generate .sto files for OpenSense
            file_operations.json_to_sto(file_name, imu_labels, filter=True)
            break
        
        except Exception as error:
            print("Unhandled exception.")
            print(error)
            print(traceback.format_exc())
            serial_op.stop_streaming(serial_port, imu_configuration['logical_ids'])
            break 