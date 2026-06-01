import lara_opensense.imu_simulator as imu_simulator
from lara_opensense.segment import Segment
import numpy as np
import warnings
import os
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    
    rot_seq = 'yzx'
    
    folder = 'Projects/Experiments/precision_test/captures'
    captures = ['x_axis_test', 'y_axis_test', 'z_axis_test']
    trial_num = 5

    for i, capture in enumerate(captures):
        total_rmse = {'imu_1_x':[], 'imu_1_y':[], 'imu_1_z':[],
                      'imu_2_x':[], 'imu_2_y':[], 'imu_2_z':[]}
        
        for n in range(trial_num):
            try:
                json_file = os.path.join(folder, f'{capture}_{n}.json')
                # json_file = 'precision_test/x_axis_test_2.json'

                df = imu_simulator.getDataframe(json_file)
                rotations = imu_simulator.build_rotations(df)

                seg_imu_2 = Segment(label='imu_2', imu_label='imu_2',
                                    parent=None, length=25, initial_angle_deg=None)
                seg_imu_1 = Segment(label='imu_1', imu_label='imu_1',
                                    parent=seg_imu_2, length=25, initial_angle_deg=None)
                
                chain = [seg_imu_2, seg_imu_1]

                df_angles = imu_simulator.calculate_joint_angles(chain, rotations, rot_seq=rot_seq)

                for angle in df_angles:
                    # print(angle)
                    total_rmse[angle].append(float(np.sqrt(np.mean(df_angles[angle]**2))))
                    # print(total_rmse[angle])

            except:
                # print(f"Erro no arquivo {json_file}")
                continue
        
        
        if i == 0:
            print("_____________________________________________________________")
            print("|               |              |              |              |")
            print("|     teste     |    x axis    |    y axis    |    z axis    |")
        print("|_______________|______________|______________|______________|")
        print("|               |              |              |              |")
        print(f"|  {capture}  | {np.mean(total_rmse['imu_1_x']):.2f} +- {np.std(total_rmse['imu_1_x']):.2f} | {np.mean(total_rmse['imu_1_y']):.2f} +- {np.std(total_rmse['imu_1_y']):.2f} | {np.mean(total_rmse['imu_1_z']):.2f} +- {np.std(total_rmse['imu_1_z']):.2f} |")
        if i == 2:
            print("|_______________|______________|______________|______________|")

