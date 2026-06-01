import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import interp1d
from scipy.signal import butter, filtfilt


def quaternionToEuler(quaternion, sequence='xyz', degrees=False):

    q = np.array(quaternion)

    rot = R.from_quat(q)

    return rot.as_euler(sequence, degrees=degrees)


def getRotationMatrixFromEuler(euler_angles):

    alpha = euler_angles[0]
    beta = euler_angles[1]
    gamma = euler_angles[2]

    rot_x = np.array([[1,             0,              0],
                      [0, np.cos(alpha), -np.sin(alpha)],
                      [0, np.sin(alpha),  np.cos(alpha)]])
    
    rot_y = np.array([[ np.cos(beta), 0, np.sin(beta)],
                      [            0, 1,            0],
                      [-np.sin(beta), 0, np.cos(beta)]])
    
    rot_z = np.array([[np.cos(gamma), -np.sin(gamma), 0],
                      [np.sin(gamma),  np.cos(gamma), 0],
                      [            0,              0, 1]])
    
    return rot_z @ rot_y @ rot_x
    

def getEulerAnglesFromRotation(rotation_matrix):
    R_11 = rotation_matrix[0][0]
    R_21 = rotation_matrix[1][0]
    R_31 = rotation_matrix[2][0]
    R_32 = rotation_matrix[2][1]
    R_33 = rotation_matrix[2][2]

    # Rotação em X (alpha)
    alpha = np.atan2(R_32, R_33) * 180 / np.pi
    
    # Rotação em Y (beta)
    seno_beta = np.clip(-R_31, -1.0, 1.0) 
    beta = np.asin(seno_beta) * 180 / np.pi
    
    # Rotação em Z (gamma)
    gamma = np.atan2(R_21, R_11) * 180 / np.pi

    return np.array([alpha, beta, gamma])

def getTransformMatrix(rot_matrix, origin_point):

    T = np.eye(4)

    T[0:3, 0:3] = rot_matrix
    
    T[0:3, 3] = origin_point.reshape(3,)
    
    return T


def shift_imu_readings(df, columns_to_shift, shift_amount):

    df_shifted = df.copy()
    
    for col in columns_to_shift:
        df_shifted[col] = df_shifted[col].shift(periods=shift_amount)
    
    df_shifted = df_shifted.dropna(subset=columns_to_shift)
    df_shifted = df_shifted.reset_index(drop=True)
        
    return df_shifted


def getDataframe(json_file, resampling_rate=None, filter_data=True, cutoff_freq=3.0, filter_order=4, phase_correction=0):
    # Read json and format data
    df = pd.read_json(json_file, lines=True)
    # df = shift_imu_readings(df, ['tibia_r_imu'], 100)
    df['time'] = df['time'].astype(float)

    cols_imu = [c for c in df.columns if 'imu' in c.lower()]

    def parse_imu_string(imu_str):
        """ Transforma "[0.66503 0.33861 0.18432 0.63961]" numa lista de 4 floats."""
        clean_str = imu_str.replace('[', '').replace(']', '').strip()
        values = clean_str.split()
        return [float(x) for x in values]
    
    for col in cols_imu:
        df[col] = df[col].apply(parse_imu_string)

    # Descobrir a frequência de amostragem para o filtro
    if resampling_rate is not None:
        fs = resampling_rate
    else:
        # Se não houver resampling, estima a frequência média baseada no tempo
        fs = 1.0 / np.mean(np.diff(df['time'].values))

    # Configuração do Filtro Butterworth Low-Pass
    if filter_data:
        nyquist = 0.5 * fs
        normal_cutoff = cutoff_freq / nyquist
        # btype='low' suaviza movimentos bruscos e remove ruídos de alta frequência
        b, a = butter(filter_order, normal_cutoff, btype='low', analog=False)

    # Novo vetor de tempo (se houver resampling)
    t_original = df['time'].values
    if resampling_rate is not None:
        t_new = np.linspace(t_original[0], t_original[-1], int((t_original[-1] - t_original[0]) * resampling_rate))
    else:
        t_new = t_original

    def process_quaternions(col_name):
        quats = np.array(df[col_name].tolist())
        
        # 1. Interpolação (Resampling)
        if resampling_rate is not None:
            f = interp1d(t_original, quats, axis=0, kind='linear')
            quats = f(t_new)

        # 2. Filtragem Butterworth
        if filter_data:
            # filtfilt garante que a fase não seja distorcida (sem atraso no tempo)
            quats = filtfilt(b, a, quats, axis=0)

        # 3. Normalização (Crucial para quatérnios após interpolação ou filtragem!)
        norms = np.linalg.norm(quats, axis=1)[:, np.newaxis]
        return quats / norms

    # Aplica o processamento (Interpolação -> Filtro -> Normalização)
    if resampling_rate is not None:
        df_new = pd.DataFrame()
        df_new['time'] = t_new
        for col in cols_imu:
            df_new[f"{col}"] = list(process_quaternions(col))
        df = df_new
    else:
        for col in cols_imu:
            df[col] = list(process_quaternions(col))

    # Convert Quaternion in Euler Angles
    for col in cols_imu:
        df[f"{col}_euler"] = df[col].apply(quaternionToEuler)

    return df


def getSystemRotationMatrixes(df, calibrate_imu_position=True, initial_angles=None):

    euler_angles_imu1 = df[f'femur_r_imu_euler'].to_numpy()
    euler_angles_imu2 = df[f'tibia_r_imu_euler'].to_numpy()

    rot_imu1_global = [getRotationMatrixFromEuler(euler_angles) for euler_angles in euler_angles_imu1]
    rot_imu2_global = [getRotationMatrixFromEuler(euler_angles) for euler_angles in euler_angles_imu2]

    if calibrate_imu_position:

        rot_shoulder_global_0 = getRotationMatrixFromEuler([0,0,initial_angles[0]])
        rot_shoulder_imu1 = rot_imu1_global[0].T @ rot_shoulder_global_0
        rot_shoulder_global = [rot_imu1_g @ rot_shoulder_imu1 for rot_imu1_g in rot_imu1_global]

        rot_elbow_global_0 = getRotationMatrixFromEuler([0,0,-np.pi/2])
        rot_elbow_imu2 = rot_imu2_global[0].T @ rot_elbow_global_0
        rot_elbow_global = [rot_imu2_g @ rot_elbow_imu2 for rot_imu2_g in rot_imu2_global]
    else:
        rot_shoulder_global = rot_imu1_global
        rot_elbow_global = rot_imu2_global
    
    return rot_shoulder_global, rot_elbow_global


def getPoints(rot_shoulder_global, rot_elbow_global):
    L1 = 1
    L2 = 1  

    p_origin_shoulder_G = np.array([0, 0, 0])
    p_origin_elbow_S_4 = np.array([L1, 0, 0, 1])
    p_hand_E_4 = np.array([L2, 0, 0, 1])

    transform_matrices_shoulder_global = [getTransformMatrix(rot_matrix, p_origin_shoulder_G) for rot_matrix in rot_shoulder_global]

    p_origin_elbow_G = np.array([transform_matrix @ p_origin_elbow_S_4.T for transform_matrix in transform_matrices_shoulder_global])[:, 0:3]

    transform_matrices_elbow_global = [getTransformMatrix(rot_matrix, origin_point) for rot_matrix, origin_point in zip(rot_elbow_global, p_origin_elbow_G)]

    p_hand_G = np.array([transform_matrix @ p_hand_E_4.T for transform_matrix in transform_matrices_elbow_global])[:, 0:3]

    return p_origin_elbow_G, p_hand_G


def show_animation(p_elbow, p_hand, time, interval, tamanho_rastro=35):
    """
    Anima dois vetores 3D a partir de matrizes de coordenadas.
    
    Args:
        p_elbow (np.array): Matriz (N, 3) com coordenadas [x, y, z]
        p_hand (np.array): Matriz (N, 3) com coordenadas [x, y, z]
        intervalo (int): Tempo entre frames em milissegundos
    """

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Determina os limites dinamicamente com base nos dados
    all_data = np.vstack((p_elbow, p_hand))
    limit = np.max(np.abs(all_data)) * 1.1

    p_hand_rel = p_hand-p_elbow

    # Inicializa os vetores
    q1 = ax.quiver(0, 0, 0, p_elbow[0,0], p_elbow[0,1], p_elbow[0,2], color='red', label='Braço')
    q2 = ax.quiver(p_elbow[0,0], p_elbow[0,1], p_elbow[0,2], p_hand_rel[0,0], p_hand_rel[0,1], p_hand_rel[0,2], color='blue', label='Antebraço')

    trajeto_line, = ax.plot([], [], [], color='green', linestyle='-', linewidth=1.5, alpha=0.7, label='Trajeto da Mão')
    
    time_text = ax.text2D(0.05, 0.95, "", transform=ax.transAxes)
    
    ax.set_xlim([-limit, limit])
    ax.set_ylim([-limit, limit])
    ax.set_zlim([-limit, limit])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title("IMU MoCap LARA")
    ax.legend()
    ax.view_init(elev=90, azim=270)

    def update(num):
        nonlocal q1, q2
        q1.remove()
        q2.remove()
        
        # Desenha os novos vetores para o frame atual
        q1 = ax.quiver(0, 0, 0, p_elbow[num,0], p_elbow[num,1], p_elbow[num,2], color='red', arrow_length_ratio=0.15)
        q2 = ax.quiver(p_elbow[num,0], p_elbow[num,1], p_elbow[num,2], p_hand_rel[num,0], p_hand_rel[num,1], p_hand_rel[num,2], 
                       color='blue', arrow_length_ratio=0.15)
        
        start_idx = max(0, num - tamanho_rastro)
        
        trajeto_line.set_data(p_hand[start_idx:num+1, 0], p_hand[start_idx:num+1, 1])
        trajeto_line.set_3d_properties(p_hand[start_idx:num+1, 2])
        
        # Atualiza o contador de tempo na tela
        time_text.set_text(f"Tempo: {time[num]:.2f}s")

        return q1, q2, time_text

    # Cria a animação
    animation = FuncAnimation(fig, update, frames=len(p_elbow), interval=interval)
    
    plt.show()

# --- Exemplo de Uso ---
if __name__ == "__main__":

    # SETUP

    json_file = 'tchau.json'

    resampling_rate = 15
    
    df = getDataframe(json_file, resampling_rate=resampling_rate)

    time = df['time'].to_numpy()

    # CALCULO ROTACOES E POSICOES

    rot_shoulder_global, rot_elbow_global = getSystemRotationMatrixes(df, calibrate_imu_position=False)

    rot_elbow_shoulder = [rot_s_g.T @ rot_e_g for rot_s_g, rot_e_g in zip(rot_shoulder_global, rot_elbow_global)]

    knee_angles = np.array([getEulerAnglesFromRotation(rot_e_s.T) for rot_e_s in rot_elbow_shoulder])

    # knee_angles = np.array([getEulerAnglesFromRotation(getRotationMatrixFromEuler([0,0,np.pi/4]) @ getRotationMatrixFromEuler([0,0,0])) for rot_e_s in rot_elbow_shoulder])

    print(knee_angles)

    initial_torso_angle = np.pi/4
    rot_torso_global = getRotationMatrixFromEuler([0,0,initial_torso_angle])
    rot_hip_torso = [rot_torso_global @ rot_s_g for rot_s_g in rot_shoulder_global]

    hip_angles = np.array([getEulerAnglesFromRotation(rot_h_t) for rot_h_t in rot_hip_torso])
    # print(hip_angles)

    p_elbow, p_hand = getPoints(rot_shoulder_global, rot_elbow_global)

    knee_angles2 = np.array([np.acos((p_e @ (p_h-p_e))/(np.linalg.norm(p_e)*np.linalg.norm(p_h-p_e))) for p_e, p_h in zip(p_elbow, p_hand)])
    print(knee_angles2*180/np.pi)

    # GERACAO DOS GRAFICOS E ANIMACAO

    # fig, ax = plt.subplots()
    # ax.plot(p_hand[:, 0], p_hand[:,1])
    # plt.show()

    fig, ax = plt.subplots()
    ax.plot(time, knee_angles[:, 1])
    ax.plot(time, knee_angles2*180/np.pi)
    ax.plot(time, hip_angles[:,2])
    plt.show()
    
    # show_animation(p_elbow, p_hand, time, 1000/resampling_rate)