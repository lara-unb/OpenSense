import utils.file_operations as file_operations

file_name = 'data/example'

imu_labels = ['femur_r_imu', 'tibia_r_imu']

file_operations.json_to_sto(file_name, imu_labels)
file_operations.json_to_sto(file_name, imu_labels, filter=True)