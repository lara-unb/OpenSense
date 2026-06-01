import os
import lara_opensense.imu_capture as imu_capture


def standard_capture(imuSystem, file_preffix, trial_num):

    for i in range(trial_num):
        try:
            input(f"Aperte Enter para começar a captura {file_preffix}_{i}")
            file_name = f"{file_preffix}_{i}"
            imu_capture.IMUCaptureQuaternion(imuSystem, file_name, duration=10)
        except:
            print(f"Erro na captura {i}")


if __name__ == "__main__":

    imus = {"imu_1": 9,
            "imu_2": 10}
    
    folder = 'precision_test'
    captures = ['x_axis_test', 'y_axis_test', 'z_axis_test']
    trial_num = 5

    imuSystem = imu_capture.configureIMU(imus)
    print("configuração ok")

    if imuSystem is not None:
        imu_capture.IMUCaptureQuaternion(imuSystem, os.path.join(folder,'static_cal'), duration=3)
    print("calibracao estática ok")

    for capture in captures:
        standard_capture(imuSystem, os.path.join(folder, capture), trial_num)

