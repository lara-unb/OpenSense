import numpy as np
import utils.serial_operations as serial_op
import utils.quaternion_operations as quaternions_op
import utils.euler_angle_operations as euler_op
import time

# data strategies
data_strategies = {
    0: {
        "extract": serial_op.extract_quaternions,
        "key": "quaternions",
        "angle_function": quaternions_op.calculate_angle_between_quaternions
    },
    1: {
        "extract": serial_op.extract_euler_angles,
        "key": "euler_vector", # Corrigido para bater com o return da função
        "angle_function": euler_op.calculate_angle_between_euler_angles
    },
    2: {
        "extract": serial_op.extract_rotation_matrix,
        "key": "rotation_matrix", # Corrigido para bater com o return da função
        "angle_function": None
    },
    37: {
        "extract": serial_op.extract_gyro,
        "key": "gyro",
        "angle_function": None
    },
    38: {
        "extract": serial_op.extract_accel,
        "key": "accel",
        "angle_function": None
    },
    250: {
        "extract": serial_op.extract_button,
        "key": "button",
        "angle_function": None
    }
}

def initialize_dongle(imus):
    imu_ids = list(imus.values())
    serial_port = serial_op.initialize_dongle(imu_ids)
    return serial_port

class IMU:
    def __init__(self, serial_port, imus):
        self.serial_port = serial_port
        self.imu_labels = list(imus.keys())
        self.imu_ids = list(imus.values())
        self.imus = imus
        self.streaming_commands = []
        self.streaming_indices = {}
    
    def configure(self, disableCompass = True, disableGyro = False, disableAccelerometer = False, gyroAutoCalib = True, 
                    filterMode = 1, axisDirections = 0, tareSensor = True, show_quaternion = True, show_euler_angle = True, show_accel = False, show_gyro = False,
                    show_compass = False, show_rotation_matrix = False, tareWithQuaternion = None, show_button = False, baudrate = 115200, timestamp = True):
        
        imu_ids = self.imu_ids

        streaming_commands = list()

        streaming_codes = [(show_quaternion, 0),
                        (show_euler_angle, 1),
                        (show_accel, 39),
                        (show_gyro, 38),
                        (show_compass, 40),
                        (show_rotation_matrix, 2),
                        (show_button, 250)]

        for show, code in streaming_codes:
            if show:
                streaming_commands.append(code)
                print(code)

        if len(streaming_commands) < 8:
            remaining = 8 - len(streaming_commands)
            streaming_commands.extend([255] * remaining)

        self.streaming_commands = streaming_commands

        imu_configuration = {
            "disableCompass": disableCompass, #command 109
            "disableGyro": disableGyro, # command 107
            "disableAccelerometer": disableAccelerometer, #108
            "gyroAutoCalib": gyroAutoCalib, #command 165
            "filterMode": filterMode, #command 123
            "axisDirections": axisDirections, # X:Forward, Y:Up, Z:Right -> OpenSim Standard
            "tareSensor": tareSensor, #command 96
            "tareWithQuaternion": tareWithQuaternion,
            "logical_ids": imu_ids,
            "streaming_commands": streaming_commands, #command 80 - ccepts a list of 8 bytes
            "baudrate": baudrate, #command 231,
            # to implement yet
            "buttonState": show_button
        }

        serial_op.revised_initialize_imu(self.serial_port, imu_configuration)
        time.sleep(2)
        print()

        return streaming_commands

    def read_data(self):
        serial_port = self.serial_port
        bytes_to_read = serial_port.in_waiting

        if bytes_to_read > 0:
            data = serial_port.read(bytes_to_read)
            
            if data[0] != 0 and len(data) <=3:
                print('Corrupted data read.')
            else: 
                return data
        

    def extract_data(self, data, type_of_data, imu_id):
        # Set parameters for IMU configuration
        # streaming commands:
        # 0: get tared orientation as quaternions
        # 1: get tared orientation as euler angles
        # 2: rotation matrix !!
        # 37: get all corrected component sensor data
        # 38: get corrected gyro rate
        # 39: get corrected accelerometer vector
        # 40: get corrected magnetometer data !!

        streamming_slots = self.streaming_commands

        current_strategy = data_strategies.get(type_of_data)

        value = current_strategy["extract"](data, streamming_slots.index(type_of_data))

        if data[1] == imu_id:
            #timestamp = serial_op.get_timestamp(serial_port, imu_id)
            #print(timestamp)
            return value

                # Check which IMU is sending information
    
    def stop_streaming(self):
        serial_op.stop_streaming(self.serial_port, self.imu_ids)
        serial_op.manual_flush(self.serial_port)


    def start_streaming(self, frequency, timestamp = False, duration = 4294967295, delay =  0):
            
            # TODO: implementar configuração de streaming e coleta de timestamp
            interval = 1000000 / frequency

            if frequency == 0:
                interval = 0

            # minimum interval is 1000 or 0, thus, the maximum frequency is 1000Hz 
            streaming_configuration = {
                "interval": interval, # microseconds, how often the data will be outputed
                "duration": duration, #by standart, indefinite time
                "delay": delay,
                "timestamp": timestamp,
                "logical_ids": self.imu_ids
            }

            # serial_op.configure_streaming(self.serial_port, streaming_configuration)

            print("Starting streaming.")
            # Start streaming
            serial_op.start_streaming(self.serial_port, streaming_configuration['logical_ids'])
            
            print("IMU's ready to use.")
