import lara_opensense.imu_capture as imu_capture
import lara_opensense.file_operations as file_operations
import traceback

    
imus = {"femur_r_imu": 4,
        "tibia_r_imu": 6}

imuSystem = None

while True:
    print("\nSelecione a ação desejada:")
    user_input = input("1) Configuração das IMUs\n2) Captura de calibração estática\n3) Captura de movimento\n4) Finalizar sessão\n")

    if user_input == "1":
        try:
            imuSystem = imu_capture.configureIMU(imus)
        except Exception as error:
                print("Unhandled exception.caraio")
                print(error)
                print(traceback.format_exc())


    elif user_input == "2":
        if imuSystem is not None:
            try:
                file_name = input("Digite o nome do arquivo de calibração\n")
                imu_capture.IMUCaptureQuaternion(imuSystem, file_name, duration=3)
                file_operations.json_to_sto(file_name, imuSystem.imu_labels, static=True)
            except Exception as error:
                print("Unhandled exception.caraio2")
                print(error)
                print(traceback.format_exc())
                imuSystem.stop_streaming()
        else:
            print("\n--- Configure as IMUs antes de realizar a captura! ---")

    elif user_input == "3":
        if imuSystem is not None:
            try:
                file_name = input("Digite o nome do arquivo de captura\n")
                imu_capture.IMUCaptureQuaternion(imuSystem, file_name)
                file_operations.json_to_sto(file_name, imuSystem.imu_labels)
            except Exception as error:
                print("Unhandled exception.caraio3")
                print(error)
                print(traceback.format_exc())
                imuSystem.stop_streaming()
        else:
            print("\n--- Configure as IMUs antes de realizar a captura! ---")
    
    elif user_input == "4":
        print("Sessão finalizada")
        break

    else:
        print("Selecione uma opção válida")
        continue
