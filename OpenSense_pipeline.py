import opensim as osim
from math import pi

def IMUPlacer(model_file, calibration_file):

    # Instantiate an IMUPlacer object
    imuPlacer = osim.IMUPlacer()
    sensor_to_opensim_rotations = osim.Vec3(0, 0, 0) # The rotation of IMU data to the OpenSim world frame

    # Set properties for the IMUPlacer
    imuPlacer.set_model_file(model_file)
    imuPlacer.set_orientation_file_for_calibration(calibration_file)
    imuPlacer.set_sensor_to_opensim_rotations(sensor_to_opensim_rotations)

    # Run the IMUPlacer
    imuPlacer.run(False)

    # Get the model with the calibrated IMU
    model = imuPlacer.getCalibratedModel()

    # Print the calibrated model to file.
    model.printToXML('calibrated_' + model_file)


def IMUInverseKinematics(model_file, orientations_file, time=None):

    sensor_to_opensim_rotation = osim.Vec3(0, 0, 0) # The rotation of IMU data to the OpenSim world frame
    
    # startTime = 1.002873659          # Start time (in seconds) of the tracking simulation. 
    # endTime = 21.89439249             # End time (in seconds) of the tracking simulation.

    resultsDirectory = 'IKResults'
    movFile = resultsDirectory + '/ik_' + orientations_file.split('/')[-1][:-4] + '.mot'

    # Instantiate an InverseKinematicsTool
    imuIK = osim.IMUInverseKinematicsTool()
    
    # Set tool properties
    imuIK.set_model_file(model_file)
    imuIK.set_orientations_file(orientations_file)
    imuIK.set_sensor_to_opensim_rotations(sensor_to_opensim_rotation)
    imuIK.set_results_directory(resultsDirectory)

    # Set time range in seconds
    # imuIK.set_time_range(0, startTime) 
    # imuIK.set_time_range(1, endTime)   

    # Run IK
    imuIK.run(False)


if __name__ == "__main__":
    # Set variables to use
    modelFile_cal = 'model.osim'          # The path to an input model
    calibrationFile = 'examples/exampleLARA/example_filtered_pos.sto'   # The path to orientation data for calibration

    IMUPlacer(modelFile_cal, calibrationFile)

    modelFile_ik = 'calibrated_model.osim'                # The path to an input model 
    orientationsFile = 'examples/exampleLARA/example_filtered_mov.sto'   # The path to orientation data for calibration 

    IMUInverseKinematics(modelFile_ik, orientationsFile) 

