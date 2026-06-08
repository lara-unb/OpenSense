import lara_opensense.imu_simulator as imu_simulator
from lara_opensense.segment import Segment

json_file = 'Training/CinematicaInversa/mov_arm.json'

rot_seq = 'zyx'

resampling_rate = 25

df = imu_simulator.getDataframe(json_file, resampling_rate=resampling_rate)
time = df['time'].to_numpy()

rotations = imu_simulator.build_rotations(df)


seg_arm = Segment(label='arm', imu_label='femur_r_imu',
                    parent=None, length=25, initial_angle_deg=None)
seg_forearm = Segment(label='forearm', imu_label='tibia_r_imu',
                    parent=seg_arm, length=25, initial_angle_deg=None)
skeleton = [seg_arm, seg_forearm]


imu_simulator.show_animation_arrows(skeleton, rotations, time, 1000 / resampling_rate, rot_seq=rot_seq, trail_length=100)