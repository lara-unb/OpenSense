import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import interp1d
from scipy.signal import butter, filtfilt

    

def getTransformMatrix(rot_matrix, origin_point):

    T = np.eye(4)

    T[0:3, 0:3] = rot_matrix
    
    T[0:3, 3] = origin_point.reshape(3,)
    
    return T


def getDataframe(json_file, resampling_rate=None, filter_data=True, cutoff_freq=3.0, filter_order=4):
    # Read json and format data
    df = pd.read_json(json_file, lines=True)
    # df = df[df['time']>60]
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

    return df


def getSystemRotationMatrixes(df, calibrate_imu_position=True, initial_angles=None):

    quaternions_imu1 = df[f'femur_r_imu'].to_numpy()
    quaternions_imu2 = df[f'tibia_r_imu'].to_numpy()
    # quaternions_gear = df[f'Gear_imu'].to_numpy()

    rot_imu1_global = [R.from_quat(quaternion) for quaternion in quaternions_imu1]
    rot_imu2_global = [R.from_quat(quaternion) for quaternion in quaternions_imu2]
    # rot_gear_global = [R.from_quat(quaternion) for quaternion in quaternions_gear]
    rot_gear_global = None

    if calibrate_imu_position:

        # a = [np.pi/2,0,0]
        # a = [0,0,0]
        initial_shoulder_angle = 90
        initial_elbow_angle = 90

        rot_shoulder_global_0 = R.from_euler(seq=rot_seq, angles=[-initial_shoulder_angle   *np.pi/180,0,0])
        rot_shoulder_imu1 = rot_imu1_global[0].inv() * rot_shoulder_global_0
        # rot_shoulder_imu1 = R.from_euler(seq=rot_seq, angles=a)
        # rot_shoulder_global = [rot_shoulder_imu1 * rot_imu1_g for rot_imu1_g in rot_imu1_global]
        rot_shoulder_global = [rot_imu1_g * rot_shoulder_imu1 for rot_imu1_g in rot_imu1_global]

        rot_elbow_global_0 =  R.from_euler(seq=rot_seq, angles=[-initial_elbow_angle*np.pi/180,0,0])
        rot_elbow_imu2 = rot_imu2_global[0].inv() * rot_elbow_global_0
        # rot_elbow_imu2 = R.from_euler(seq=rot_seq, angles=a)
        rot_elbow_global = [rot_imu2_g * rot_elbow_imu2 for rot_imu2_g in rot_imu2_global]

    else:
        rot_shoulder_global = rot_imu1_global
        rot_elbow_global = rot_imu2_global
    
    return rot_shoulder_global, rot_elbow_global, rot_gear_global


def getPoints(rot_shoulder_global, rot_elbow_global, rot_gear_global):
    L1 = 33.5
    L2 = 28.5
    L_gear = 15

    p_origin_gear_G = np.array([10, 0, 10])
    p_origin_Gear_g_4 = np.array([L_gear, 0, 0, 1])
    p_origin_shoulder_G = np.array([0, 0, 0])
    p_origin_elbow_S_4 = np.array([L1, 0, 0, 1])
    p_hand_E_4 = np.array([L2, 0, 0, 1])

    # transform_matrices_gear_global = [getTransformMatrix(rot_matrix.as_matrix(), p_origin_gear_G) for rot_matrix in rot_gear_global]

    # p_gear_G = np.array([transform_matrix @ p_origin_Gear_g_4.T for transform_matrix in transform_matrices_gear_global])[:, 0:3]
    p_gear_G = None

    transform_matrices_shoulder_global = [getTransformMatrix(rot_matrix.as_matrix(), p_origin_shoulder_G) for rot_matrix in rot_shoulder_global]

    p_origin_elbow_G = np.array([transform_matrix @ p_origin_elbow_S_4.T for transform_matrix in transform_matrices_shoulder_global])[:, 0:3]

    transform_matrices_elbow_global = [getTransformMatrix(rot_matrix.as_matrix(), origin_point) for rot_matrix, origin_point in zip(rot_elbow_global, p_origin_elbow_G)]

    p_hand_G = np.array([transform_matrix @ p_hand_E_4.T for transform_matrix in transform_matrices_elbow_global])[:, 0:3]

    return p_origin_elbow_G, p_hand_G, p_gear_G


def getPoints_arrows(rot_shoulder_global, rot_elbow_global):
    L1 = 45

    p_origin_shoulder_G = np.array([0, 0, 0])
    p_shoulder_y_S = np.array([0, 20, 0, 1])
    p_shoulder_z_S = np.array([0, 0, 20, 1])
    p_origin_elbow_S_4 = np.array([L1, 0, 0, 1])
    p_elbow_y_S = np.array([0, 20, 0, 1])
    p_elbow_z_S = np.array([0, 0, 20, 1])

    transform_matrices_shoulder_global = [getTransformMatrix(rot_matrix.as_matrix(), p_origin_shoulder_G) for rot_matrix in rot_shoulder_global]

    p_origin_elbow_G = np.array([transform_matrix @ p_origin_elbow_S_4.T for transform_matrix in transform_matrices_shoulder_global])[:, 0:3]
    p_shoulder_y_G = np.array([transform_matrix @ p_shoulder_y_S.T for transform_matrix in transform_matrices_shoulder_global])[:, 0:3]
    p_shoulder_z_G = np.array([transform_matrix @ p_shoulder_z_S.T for transform_matrix in transform_matrices_shoulder_global])[:, 0:3]

    transform_matrices_elbow_global = [getTransformMatrix(rot_matrix.as_matrix(), origin_point) for rot_matrix, origin_point in zip(rot_elbow_global, p_origin_elbow_G)]

    p_elbow_y_G = np.array([transform_matrix @ p_elbow_y_S.T for transform_matrix in transform_matrices_elbow_global])[:, 0:3]
    p_elbow_z_G = np.array([transform_matrix @ p_elbow_z_S.T for transform_matrix in transform_matrices_elbow_global])[:, 0:3]
    

    return p_shoulder_y_G, p_shoulder_z_G, p_elbow_y_G, p_elbow_z_G


def getPoints_angles(knee_angles, hip_angles):
    L1 = 45
    L2 = 48

    p_origin_elbow_G = np.array([[L1*np.cos(hip*np.pi/180), L1*np.sin(hip*np.pi/180), 0] for hip in hip_angles[:,0]])
    sum_angles = 180-knee_angles+hip_angles-90
    p_hand_G = np.array([[L2*np.sin(sum*np.pi/180), -L2*np.cos(sum*np.pi/180), 0] for sum in sum_angles[:,0]])
    p_hand_G = p_hand_G + p_origin_elbow_G

    return p_origin_elbow_G, p_hand_G

def getPoints_kinovea(knee_angles, hip_angles):
    L1 = 35
    L2 = 32

    new_hip_angles = hip_angles + 45
    p_origin_elbow_G = np.array([[L1*np.sin(hip*np.pi/180), -L1*np.cos(hip*np.pi/180), 0] for hip in new_hip_angles])
    sum_angles = knee_angles+180-new_hip_angles
    p_hand_G = np.array([[L2*np.sin(sum*np.pi/180), L2*np.cos(sum*np.pi/180), 0] for sum in sum_angles])
    p_hand_G = p_hand_G + p_origin_elbow_G

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
    ax.view_init(elev=90, azim=2700)
    # ax.view_init(elev=180, azim=0)

    def update(num):
        nonlocal q1, q2
        q1.remove()
        q2.remove()
        
        # Desenha os novos vetores para o frame atual
        q1 = ax.quiver(0, 0, 0, p_elbow[num,0], p_elbow[num,1], p_elbow[num,2], color='red', arrow_length_ratio=0.15)
        q2 = ax.quiver(p_elbow[num,0], p_elbow[num,1], p_elbow[num,2], p_hand_rel[num,0], p_hand_rel[num,1], p_hand_rel[num,2], 
                       color='blue', arrow_length_ratio=0.15)
        
        start_idx = max(0, num - tamanho_rastro)
        
        trajeto_line.set_data(p_elbow[start_idx:num+1, 0], p_elbow[start_idx:num+1, 1])
        trajeto_line.set_3d_properties(p_elbow[start_idx:num+1, 2])
        
        # Atualiza o contador de tempo na tela
        time_text.set_text(f"Tempo: {time[num]:.2f}s")

        return q1, q2, time_text

    # Cria a animação
    animation = FuncAnimation(fig, update, frames=len(p_elbow), interval=interval)
    
    plt.show()


def show_animation_arrows(points, time, interval, tamanho_rastro=35):
    """
    Anima dois vetores 3D a partir de matrizes de coordenadas.
    
    Args:
        p_elbow (np.array): Matriz (N, 3) com coordenadas [x, y, z]
        p_hand (np.array): Matriz (N, 3) com coordenadas [x, y, z]
        intervalo (int): Tempo entre frames em milissegundos
    """

    p_shoulder_y_G, p_shoulder_z_G, p_elbow, p_elbow_y_G, p_elbow_z_G, p_hand = points

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Determina os limites dinamicamente com base nos dados
    all_data = np.vstack((p_elbow, p_hand))
    limit = np.max(np.abs(all_data)) * 1.1

    p_hand_rel = p_hand-p_elbow
    p_elbow_y_G_rel = p_elbow_y_G-p_elbow
    p_elbow_z_G_rel = p_elbow_z_G-p_elbow

    # Inicializa os vetores
    q1 = ax.quiver(0, 0, 0, p_elbow[0,0], p_elbow[0,1], p_elbow[0,2], color='red', label='Braço')
    q2 = ax.quiver(p_elbow[0,0], p_elbow[0,1], p_elbow[0,2], p_hand_rel[0,0], p_hand_rel[0,1], p_hand_rel[0,2], color='blue', label='Antebraço')
    qsy = ax.quiver(0, 0, 0, p_shoulder_y_G[0,0], p_shoulder_y_G[0,1], p_shoulder_y_G[0,2], color='green', label='Braço_Y')
    qsz = ax.quiver(0, 0, 0, p_shoulder_z_G[0,0], p_shoulder_z_G[0,1], p_shoulder_z_G[0,2], color='yellow', label='Braço_Z')
    qey = ax.quiver(p_elbow[0,0], p_elbow[0,1], p_elbow[0,2], p_elbow_y_G[0,0], p_elbow_y_G_rel[0,1], p_elbow_y_G_rel[0,2], color='green', label='Antebraço_Y')
    qez = ax.quiver(p_elbow[0,0], p_elbow[0,1], p_elbow[0,2], p_elbow_z_G[0,0], p_elbow_z_G_rel[0,1], p_elbow_z_G_rel[0,2], color='yellow', label='Antebraço_Z')

    trajeto_line, = ax.plot([], [], [], color='purple', linestyle='-', linewidth=1.5, alpha=0.7, label='Trajeto da Mão')
    
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
        nonlocal q1, q2, qsy, qsz, qey, qez
        q1.remove()
        q2.remove()
        qsy.remove()
        qsz.remove()
        qey.remove()
        qez.remove()
        
        # Desenha os novos vetores para o frame atual
        q1 = ax.quiver(0, 0, 0, p_elbow[num,0], p_elbow[num,1], p_elbow[num,2], color='red', arrow_length_ratio=0.15)
        q2 = ax.quiver(p_elbow[num,0], p_elbow[num,1], p_elbow[num,2], p_hand_rel[num,0], p_hand_rel[num,1], p_hand_rel[num,2], 
                       color='blue', arrow_length_ratio=0.15)
        
        qsy = ax.quiver(0, 0, 0, p_shoulder_y_G[num,0], p_shoulder_y_G[num,1], p_shoulder_y_G[num,2], color='green', label='Braço_Y')
        qsz = ax.quiver(0, 0, 0, p_shoulder_z_G[num,0], p_shoulder_z_G[num,1], p_shoulder_z_G[num,2], color='yellow', label='Braço_Z')
        qey = ax.quiver(p_elbow[num,0], p_elbow[num,1], p_elbow[num,2], p_elbow_y_G_rel[num,0], p_elbow_y_G_rel[num,1], p_elbow_y_G_rel[num,2], color='green', label='Braço_Y')
        qez = ax.quiver(p_elbow[num,0], p_elbow[num,1], p_elbow[num,2], p_elbow_z_G_rel[num,0], p_elbow_z_G_rel[num,1], p_elbow_z_G_rel[num,2], color='yellow', label='Braço_Z')
        
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

    # rot_seq = 'yzx'
    rot_seq = 'zyx'

    # json_file = 'teste_eixos.json'
    json_file = 'mov2.json'
    # json_file = 'example_trike.json'
    arquivo_kinovea = 'joelho_quadril_anatomico_angulos.csv'

    resampling_rate = 25
    
    df = getDataframe(json_file, resampling_rate=resampling_rate)

    time = df['time'].to_numpy()

    # CALCULO ROTACOES E POSICOES

    rot_shoulder_global, rot_elbow_global, rot_gear_global = getSystemRotationMatrixes(df, calibrate_imu_position=True)
    euler_shoulder = [rot.as_euler(seq=rot_seq, degrees=True) for rot in rot_shoulder_global]
    euler_elbow = [rot.as_euler(seq=rot_seq, degrees=True) for rot in rot_elbow_global]

    rot_elbow_shoulder = [rot_s_g.inv() * rot_e_g for rot_s_g, rot_e_g in zip(rot_shoulder_global, rot_elbow_global)]

    knee_angles = np.array([rot_e_s.inv().as_euler(seq=rot_seq, degrees=True) for rot_e_s in rot_elbow_shoulder])

    hip_angles = np.array([rot_s_g.as_euler(seq=rot_seq, degrees=True) for rot_s_g in rot_shoulder_global])

    forearm_angles = np.array([rot_e_g.as_euler(seq=rot_seq, degrees=True) for rot_e_g in rot_elbow_global])

    p_elbow, p_hand, p_gear = getPoints(rot_shoulder_global, rot_elbow_global, rot_gear_global)
    p_shoulder_y_G, p_shoulder_z_G, p_elbow_y_G, p_elbow_z_G = getPoints_arrows(rot_shoulder_global, rot_elbow_global)
    p_elbow_angles, p_hand_angles = getPoints_angles(knee_angles, hip_angles)

    df_kinovea = pd.read_csv(arquivo_kinovea, sep=';', decimal=',')
    p_elbow_k, p_hand_k = getPoints_kinovea(df_kinovea['joelho'].to_numpy(), df_kinovea['Quadril'].to_numpy())
    time_k = df_kinovea['Time (ms)'].to_numpy()/1000

    # knee_angles_pv = np.array([[np.acos((p_e @ (p_h-p_e))/(np.linalg.norm(p_e)*np.linalg.norm(p_h-p_e))),0,0] for p_e, p_h in zip(p_elbow, p_hand)])*180/np.pi
    # hip_angles_pv = np.array([[np.acos((p_e @ np.array([1,0,0]))/(np.linalg.norm(p_e))),0,0] for p_e in p_elbow])*180/np.pi    
    # p_elbow_pv, p_hand_pv = getPoints_angles(knee_angles_pv, hip_angles_pv)

    # GERACAO DOS GRAFICOS E ANIMACAO

    # fig, ax = plt.subplots()
    # ax.plot(time, p_hand[:])
    # ax.plot(p_hand[:, 0], p_hand[:,1])
    # # # ax.plot(p_hand_k[:, 0], p_hand_k[:,1])
    # ax.plot(p_gear[:, 2], p_gear[:,0])
    # ax.set_aspect('equal')
    # plt.show()

    # fig, ax = plt.subplots()
    # ax.plot(time, hip_angles[:])
    # ax.plot(time, hip_angles_alt[:,2])
    # ax.plot(time, teste)
    # ax.plot(time, knee_angles_pv[:,2])
    # ax.plot(time, hip_angles_pv[:,2])
    # # ax.plot(time_k, df_kinovea['joelho'].to_numpy())
    # ax.plot(time, euler_shoulder)
    # ax.plot(time, euler_elbow)
    # ax.plot(time, p_gear)
    # plt.show()

    # fig, ax = plt.subplots()
    # ax.plot(time, hip_angles[:,1])
    # ax.plot(time, forearm_angles[:,1])
    # # ax.plot(time_k, df_kinovea['Quadril'].to_numpy()-45)
    # plt.show()
    
    points = (p_shoulder_y_G, p_shoulder_z_G, p_elbow, p_elbow_y_G, p_elbow_z_G, p_hand)
    show_animation_arrows(points, time, 1000/resampling_rate, tamanho_rastro=100)
    # show_animation(p_elbow, p_hand, time, 1000/resampling_rate, tamanho_rastro=500)
    # show_animation(p_elbow_angles, p_hand_angles, time, 1000/resampling_rate, tamanho_rastro=35)
    # show_animation(p_elbow_k, p_hand_k, time_k, 1, tamanho_rastro=200)