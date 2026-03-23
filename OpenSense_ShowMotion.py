import opensim as osim

geometry_path = "C:\Opensim 4.5\Geometry"
osim.ModelVisualizer.addDirToGeometrySearchPaths(geometry_path)
modelFileName = 'calibrated_model.osim'
movFile = 'IKResults/ik_example_filtered_mov.mot'

model = osim.Model(modelFileName)
mov = osim.TimeSeriesTable(movFile)

osim.VisualizerUtilities.showMotion(model, mov)