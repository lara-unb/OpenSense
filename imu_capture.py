from utils.imu_class import IMU, initialize_dongle
import utils.file_operations as file_operations
import time
import traceback

def configureIMU(imus):

    serial_port = initialize_dongle(imus)

    imuSystem = IMU(serial_port, imus)

    imuSystem.configure(axisDirections=5)

    return imuSystem


def IMUCaptureQuaternion(imu, file_path, duration=None, discard_first_sec=True):

    startTime = time.time()
    imus_data = []
    quaternions = {}
    for i in range(len(imu.imu_labels)):
        quaternions[imu.imu_labels[i]] = [0, 0, 0, 0]
    try:
        imu.start_streaming(frequency = 100)
        imu.serial_port.reset_input_buffer()

        while_condition = True

        while while_condition:
            try:
                if duration is not None:
                    time_offset = 1 if discard_first_sec else 0
                    while_condition = (time.time() < startTime + duration + time_offset)

                data = imu.read_data()

                if data is None:
                    continue
                
                if (data[0] != 0 and len(data)<=3):
                    print('Corrupted data read.')
                    continue

                # extract quaternion data from the first IMU
                for i in range(len(imu.imus)):
                    if data[1] == imu.imu_ids[i]:
                        extracted_data = imu.extract_data(data, type_of_data=0, imu_id=imu.imu_ids[i])
                        quaternions[imu.imu_labels[i]] = extracted_data
                
                # initialize data dictionary
                imus_reading = {"time": time.time() - startTime}
                # save quaternion values
                for imu_label in imu.imu_labels:
                    imus_reading[imu_label] = str(quaternions[imu_label])

                # discard first second of IMU data readings
                if (time.time() - startTime < 1) and discard_first_sec:
                    continue
                else:
                    imus_data.append(imus_reading)

            except KeyboardInterrupt:
                print("Finished execution with control + c. ")
                break
        
        for line in imus_data:
            file_operations.write_to_json_file(file_path+'.json', line, write_mode='a')
                
        imu.stop_streaming()

    except Exception as error:
        print("Unhandled exception.")
        print(error)
        print(traceback.format_exc())
        imu.stop_streaming() 
        

if __name__ == "__main__":
    
    imus = {"tibia_r_imu": 10}

    imuSystem = None

    while True:
        print("\nSelecione a ação desejada:")
        user_input = input("1) Configuração das IMUs\n2) Captura de calibração estática\n3) Captura de movimento\n4) Finalizar sessão\n")

        if user_input == "1":
            imuSystem = configureIMU(imus)

        elif user_input == "2":
            if imuSystem is not None:
                file_name = input("Digite o nome do arquivo de calibração")
                IMUCaptureQuaternion(imuSystem, file_name, duration=0.1)
                file_operations.json_to_sto(file_name, imuSystem.imu_labels, static=True)
            else:
                print("\n--- Configure as IMUs antes de realizar a captura! ---")

        elif user_input == "3":
            if imuSystem is not None:
                file_name = input("Digite o nome do arquivo de captura")
                IMUCaptureQuaternion(imuSystem, file_name)
                file_operations.json_to_sto(file_name, imuSystem.imu_labels)
            else:
                print("\n--- Configure as IMUs antes de realizar a captura! ---")
        
        elif user_input == "4":
            print("Sessão finalizada")
            break
    
        else:
            print("Selecione uma opção válida")
            continue