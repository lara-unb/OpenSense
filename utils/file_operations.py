""" 
Defines file operation functions

"""
import json
import os
import pandas as pd
import utils.data_filters as data_filters

    
def write_to_json_file(file_out_path, data, write_mode='w'):
    """ Write video information to a json file

    Args:
        file_out_path: string with path of the text file
        data: dictionary with the data that should be writen
        write_mode: a string that defines write mode
    """

    # Create outputs directory if needed
    if not os.path.isdir("../outputs"):  os.makedirs("../outputs")

    with open(file_out_path, write_mode) as f:
        f.write(json.dumps(data))
        f.write('\n')


def prepend_multiple_lines(file_name, list_of_lines):
    """Insert given list of strings as a new lines at the beginning of a file"""
    # define name of temporary dummy file
    aux_file = file_name + '.sto'
    # open given original file in read mode and dummy file in write mode
    with open(file_name, 'r') as read_obj, open(aux_file, 'w') as write_obj:
        # Iterate over the given list of strings and write them to dummy file as lines
        for line in list_of_lines:
            write_obj.write(line + '\n')
        # Read lines from original file one by one and append them to the dummy file
        for line in read_obj:
            write_obj.write(line)
    # remove original file
    os.remove(file_name)
    # Rename dummy file as the original file
    os.rename(aux_file, file_name)


def format_to_sto(column_name, data_frame, OpenSenseQuaternion=True):

    #remove []
    data_frame[column_name] = data_frame[column_name].str.strip('[]')
    #remove first white space
    data_frame[column_name] = data_frame[column_name].str.lstrip()
    data_frame[column_name] = data_frame[column_name].str.rstrip()
    # create list spliting by whitespace
    data_frame[column_name] = data_frame[column_name].str.split(' +')

    # OpenSense requires quaternion in [w, x, y, z] format
    if OpenSenseQuaternion:
        data_frame[column_name] = data_frame[column_name].apply(lambda x: x[-1:] + x[:-1])
    #convert list to string removing space
    data_frame[column_name] = [','.join(map(str, l)) for l in data_frame[column_name]]

    return data_frame


def filter_df(df, imu_labels, OpenSenseQuaternion=True):

    df_final = df[['time']].copy()

    for label in imu_labels:
        # separate dataframe
        df_imu = df[['time', label]].copy()

        # remove doubles
        df_imu_sf = df_imu.drop_duplicates(subset=[label])
        df_imu_sf = df_imu_sf.reset_index(drop=True)

        imu_sampling_frequency = df_imu_sf.index[-1]/df_imu_sf.time.iloc[-1]

        if OpenSenseQuaternion:
            df_imu[['w', 'x', 'y', 'z']] = df_imu[label].str.split(",", expand = True)
        else:
            df_imu[['x', 'y', 'z', 'w']] = df_imu[label].str.split(",", expand = True)

        # filtering parameters
        quaternions_cols = ['w', 'x', 'y', 'z'] if OpenSenseQuaternion else ['x', 'y', 'z', 'w']
        cutoff = 1 # Hz
        order = 2

        df_imu = data_filters.filter_quaternions_dataframe(df_imu, quaternions_cols, cutoff, imu_sampling_frequency, order)

        if OpenSenseQuaternion:
            df_imu[label] = df_imu.w.astype(str) +", "+ df_imu.x.astype(str) + ", " + df_imu.y.astype(str) + ", " + df_imu.z.astype(str)
        else:    
            df_imu[label] = df_imu.x.astype(str) +", "+ df_imu.y.astype(str) + ", " + df_imu.z.astype(str) + ", " + df_imu.w.astype(str)

        df_final[label] =  df_imu[label]

    return df_final


def json_to_sto(file_name, imu_labels, filter=False):

    file_read = file_name + '.json'

    # Read JSON file to Data Frame 
    df = pd.read_json(file_read, lines=True)

    # Drop rows before 0.1s
    df = df.drop(df[df['time'] < 1].index)
    df = df.reset_index(drop=True)

    # Change data format to match .sto
    for imu_label in imu_labels:
        df = format_to_sto(imu_label, df)

    # Butter Lowpass filter
    if filter:
        df = filter_df(df, imu_labels)
    
    # Save file .sto
    position_file = file_name + '_pos.sto' if not filter else file_name + '_filtered_pos.sto'
    motion_file = file_name + '_mov.sto' if not filter else file_name + '_filtered_mov.sto'
    df.head(1).to_csv(position_file, header=True, index=None, sep='\t', mode='a')
    df.to_csv(motion_file, header=True, index=None, sep='\t', mode='a')

    # Add header to sto files
    list_of_lines = ['DataType=Quaternion', 'version=3', 'OpenSimVersion=4.5',  'endheader']
    prepend_multiple_lines(position_file, list_of_lines)
    prepend_multiple_lines(motion_file, list_of_lines)

    print(".sto files saved")

