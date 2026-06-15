import lara_opensense.imu_simulator as imu_simulator
from lara_opensense.segment import Segment
import matplotlib.pyplot as plt

json_file = 'examples/data/trike_test_ok.json'

rot_seq = 'zyx'

resampling_rate = None

df = imu_simulator.getDataframe(json_file, resampling_rate=resampling_rate, filter_data=False)
df = df[df['time']>63]
time = df['time'].to_numpy()

rotations = imu_simulator.build_rotations(df)

df_filtered = imu_simulator.getDataframe(json_file, resampling_rate=resampling_rate)
df_filtered = df_filtered[df_filtered['time']>63]
time_filtered = df_filtered['time'].to_numpy()

rotations_filtered = imu_simulator.build_rotations(df_filtered)

seg_femur = Segment(label='femur', imu_label='femur_r_imu',
                    parent=None, length=25, initial_angle_deg=None)
seg_tibia = Segment(label='tibia', imu_label='tibia_r_imu',
                    parent=seg_femur, length=25, initial_angle_deg=None)
skeleton = [seg_femur, seg_tibia]

df_angles_rel = imu_simulator.calculate_joint_angles(skeleton, rotations, rot_seq=rot_seq)

df_angles_rel_filtered = imu_simulator.calculate_joint_angles(skeleton, rotations_filtered, rot_seq=rot_seq)

fig, ax = plt.subplots()
ax.plot(time, df_angles_rel['tibia_z'], label='knee_angle')
ax.legend()
ax.grid()

fig, ax = plt.subplots()
ax.plot(time, df_angles_rel_filtered['tibia_z'], label='knee_angle_filtered')
ax.legend()
ax.grid()
plt.show()