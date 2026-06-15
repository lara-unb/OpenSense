import lara_opensense.imu_simulator as imu_simulator
from lara_opensense.segment import Segment
import matplotlib.pyplot as plt

json_file = 'examples/data/trike_test_ok.json'

rot_seq = 'zyx' # Z -> Flexao de joelho
                # Y -> Abdução de joelho
                # X -> Rotação de joelho

resampling_rate = None

# Obtenção dos dados em quaternion e cálculo das matrizes rotações 
df = imu_simulator.getDataframe(json_file, resampling_rate=resampling_rate, filter_data=False)
df = df[df['time']>63]
time = df['time'].to_numpy()

rotations = imu_simulator.build_rotations(df)

# Obtenção dos dados em quaternion e cálculo das matrizes rotações com filtro butterworth
df_filtered = imu_simulator.getDataframe(json_file, resampling_rate=resampling_rate)
df_filtered = df_filtered[df_filtered['time']>63]
time_filtered = df_filtered['time'].to_numpy()

rotations_filtered = imu_simulator.build_rotations(df_filtered)

# Definição do esqueleto
seg_femur = Segment(label='femur', imu_label='femur_r_imu',
                    parent=None, length=25, initial_angle_deg=None)
seg_tibia = Segment(label='tibia', imu_label='tibia_r_imu',
                    parent=seg_femur, length=25, initial_angle_deg=None)
skeleton = [seg_femur, seg_tibia]

# Cálculo dos ângulos do joelho
df_angles_rel = imu_simulator.calculate_joint_angles(skeleton, rotations, rot_seq=rot_seq)

df_angles_rel_filtered = imu_simulator.calculate_joint_angles(skeleton, rotations_filtered, rot_seq=rot_seq)

# Gráfico do ângulo do joelho sem filtro
fig, ax = plt.subplots()
ax.plot(time, df_angles_rel['tibia_z'], label='knee_angle')
ax.legend()
ax.grid()

# Gráfico do ângulo do joelho com filtro
fig, ax = plt.subplots()
ax.plot(time, df_angles_rel_filtered['tibia_z'], label='knee_angle_filtered')
ax.legend()
ax.grid()
plt.show()