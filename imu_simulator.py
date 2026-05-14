import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from scipy.spatial.transform import Rotation as R
from scipy.interpolate import interp1d
from scipy.signal import butter, filtfilt

from utils.segment import Segment


def getDataframe(json_file, resampling_rate=None, filter_data=True, cutoff_freq=3.0, filter_order=4):
    df = pd.read_json(json_file, lines=True)
    df['time'] = df['time'].astype(float)
    # df = df[df['time'] > 60]

    cols_imu = [c for c in df.columns if 'imu' in c.lower()]

    def parse_imu_string(imu_str):
        clean_str = imu_str.replace('[', '').replace(']', '').replace(',', ' ').strip()
        return [float(x) for x in clean_str.split()]

    for col in cols_imu:
        df[col] = df[col].apply(parse_imu_string)

    if resampling_rate is not None:
        fs = resampling_rate
    else:
        fs = 1.0 / np.mean(np.diff(df['time'].values))

    if filter_data:
        nyquist = 0.5 * fs
        normal_cutoff = cutoff_freq / nyquist
        b, a = butter(filter_order, normal_cutoff, btype='low', analog=False)

    t_original = df['time'].values
    if resampling_rate is not None:
        t_new = np.linspace(t_original[0], t_original[-1],
                            int((t_original[-1] - t_original[0]) * resampling_rate))
    else:
        t_new = t_original

    def process_quaternions(col_name):
        quats = np.array(df[col_name].tolist())
        if resampling_rate is not None:
            f = interp1d(t_original, quats, axis=0, kind='linear')
            quats = f(t_new)
        if filter_data:
            quats = filtfilt(b, a, quats, axis=0)
        norms = np.linalg.norm(quats, axis=1)[:, np.newaxis]
        return quats / norms

    if resampling_rate is not None:
        df_new = pd.DataFrame()
        df_new['time'] = t_new
        for col in cols_imu:
            df_new[col] = list(process_quaternions(col))
        df = df_new
    else:
        for col in cols_imu:
            df[col] = list(process_quaternions(col))

    return df


def build_rotations(df: pd.DataFrame) -> dict:
    """Convert imu_* DataFrame columns to dict[str, list[Rotation]] (scipy [x,y,z,w])."""
    cols_imu = [c for c in df.columns if 'imu' in c.lower()]
    return {col: [R.from_quat(q) for q in df[col].tolist()] for col in cols_imu}


def show_animation(skeleton: list, rotations: dict, time, interval,
                   rot_seq: str = 'zyx', trail_length: int = 35):
    """Animate a kinematic chain defined by a list of Segment objects."""
    n = len(time)
    colors = ['red', 'blue', 'green', 'orange', 'purple']

    origins = {seg.label: np.array([seg.get_origin(rotations, i, rot_seq) for i in range(n)])
               for seg in skeleton}
    ends = {seg.label: np.array([seg.get_end(rotations, i, rot_seq) for i in range(n)])
            for seg in skeleton}

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    all_pts = np.vstack(list(origins.values()) + list(ends.values()))
    limit = max(np.max(np.abs(all_pts)) * 1.1, 1.0)

    quivers = []
    for i, seg in enumerate(skeleton):
        o = origins[seg.label][0]
        d = ends[seg.label][0] - o
        q = ax.quiver(*o, *d, color=colors[i % len(colors)], label=seg.label)
        quivers.append(q)

    last_label = skeleton[-1].label
    trail, = ax.plot([], [], [], color='green', linewidth=1.5, alpha=0.7, label='Trajeto')
    time_text = ax.text2D(0.05, 0.95, '', transform=ax.transAxes)

    ax.set_xlim([-limit, limit])
    ax.set_ylim([-limit, limit])
    ax.set_zlim([-limit, limit])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('IMU MoCap LARA')
    ax.legend()
    ax.view_init(elev=90, azim=270)

    def update(num):
        for i, seg in enumerate(skeleton):
            quivers[i].remove()
            o = origins[seg.label][num]
            d = ends[seg.label][num] - o
            quivers[i] = ax.quiver(*o, *d, color=colors[i % len(colors)], arrow_length_ratio=0.15)

        s = max(0, num - trail_length)
        pts = ends[last_label]
        trail.set_data(pts[s:num+1, 0], pts[s:num+1, 1])
        trail.set_3d_properties(pts[s:num+1, 2])
        time_text.set_text(f'Tempo: {time[num]:.2f}s')
        return (*quivers, trail, time_text)

    anim = FuncAnimation(fig, update, frames=n, interval=interval)
    plt.show()


def show_animation_arrows(skeleton: list, rotations: dict, time, interval,
                          rot_seq: str = 'zyx', axis_length: float = 10.0,
                          trail_length: int = 35):
    """Animate kinematic chain with coordinate axes per segment."""
    n = len(time)
    seg_colors = ['red', 'blue', 'orange', 'purple']

    axes_data = {}
    for seg in skeleton:
        raw = [seg.get_axes(rotations, i, rot_seq, axis_length) for i in range(n)]
        axes_data[seg.label] = {k: np.array([a[k] for a in raw]) for k in ('origin', 'x', 'y', 'z')}

    ends = {seg.label: np.array([seg.get_end(rotations, i, rot_seq) for i in range(n)])
            for seg in skeleton}

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    all_pts = np.vstack([v for ad in axes_data.values() for v in ad.values()])
    limit = max(np.max(np.abs(all_pts)) * 1.1, 1.0)

    def _make_quivers(num):
        qs = []
        for i, seg in enumerate(skeleton):
            color = seg_colors[i % len(seg_colors)]
            ad = axes_data[seg.label]
            o = ad['origin'][num]
            e = ends[seg.label][num]
            qs.append(ax.quiver(*o, *(e - o), color=color, label=seg.label if num == 0 else ''))
            y_end = ad['y'][num]
            z_end = ad['z'][num]
            line_y, = ax.plot([o[0], y_end[0]], [o[1], y_end[1]], [o[2], y_end[2]], color='g', linewidth=0.8)
            line_z, = ax.plot([o[0], z_end[0]], [o[1], z_end[1]], [o[2], z_end[2]], color='b', linewidth=0.8)
            qs.extend([line_y, line_z])
        return qs

    quivers = _make_quivers(0)

    last_label = skeleton[-1].label
    trail, = ax.plot([], [], [], color='purple', linewidth=1.5, alpha=0.7, label='Trajeto')
    time_text = ax.text2D(0.05, 0.95, '', transform=ax.transAxes)

    ax.set_xlim([-limit, limit])
    ax.set_ylim([-limit, limit])
    ax.set_zlim([-limit, limit])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('IMU MoCap LARA')
    ax.legend()
    ax.set_aspect('equal')
    ax.view_init(elev=90, azim=270)

    def update(num):
        for q in quivers:
            q.remove()
        quivers[:] = _make_quivers(num)

        s = max(0, num - trail_length)
        pts = ends[last_label]
        trail.set_data(pts[s:num+1, 0], pts[s:num+1, 1])
        trail.set_3d_properties(pts[s:num+1, 2])
        time_text.set_text(f'Tempo: {time[num]:.2f}s')
        return (*quivers, trail, time_text)

    anim = FuncAnimation(fig, update, frames=n, interval=interval)
    plt.show()


def calculate_joint_angles(skeleton: list, rotations: dict,
                           rot_seq: str = 'zyx') -> pd.DataFrame:
    """Compute Euler joint angles for every segment at every timestep.

    Returns a DataFrame with columns {segment.label}_{axis} per rot_seq axis and one row per timestep.
    Column names reflect the actual rotation axis (e.g. rot_seq='zyx' → _z, _y, _x).
    """
    n_timesteps = len(list(rotations.values())[0])
    records = []
    for idx in range(n_timesteps):
        row = {}
        for segment in skeleton:
            angles = segment.get_joint_angle(rotations, idx, rot_seq)
            for i, axis in enumerate(rot_seq):
                row[f'{segment.label}_{axis}'] = angles[i]
        records.append(row)
    return pd.DataFrame(records)

def calculate_global_angles(skeleton: list, rotations: dict,
                           rot_seq: str = 'zyx') -> pd.DataFrame:
    """Compute Euler absolute angles for every segment at every timestep .

    Returns a DataFrame with columns {segment.label}_{axis} per rot_seq axis and one row per timestep.
    Column names reflect the actual rotation axis (e.g. rot_seq='zyx' → _z, _y, _x).
    """
    n_timesteps = len(list(rotations.values())[0])
    records = []
    for idx in range(n_timesteps):
        row = {}
        for segment in skeleton:
            angles = segment.get_absolute_angle(rotations, idx, rot_seq)
            for i, axis in enumerate(rot_seq):
                row[f'{segment.label}_{axis}'] = angles[i]
        records.append(row)
    return pd.DataFrame(records)


if __name__ == '__main__':
    # rot_seq = 'xyz'
    # rot_seq = 'zyx'
    rot_seq = 'yzx'


    # json_file = 'examples/exampleLARA_Trike/test2_trike_3imus.json'
    # json_file = 'captura_braco_arthur/mov_arthur2.json'
    # json_file = 'captura_braco_arthur/mov_body.json'  
    # json_file = 'teste_quadro.json'
    json_file = 'goniometro_livre_mov.json'

    resampling_rate = 25

    df = getDataframe(json_file, resampling_rate=resampling_rate)
    time = df['time'].to_numpy()
    rotations = build_rotations(df)

    #
    # seg_pelvis  = Segment(label='pelvis', imu_label='pelvis_imu',
    #                       parent=None, length=5, initial_angle_deg=[-90,0,0])
    seg_tibia_r = Segment(label='tibia_r', imu_label='tibia_r_imu',
                        parent=None, length=25, initial_angle_deg=None)
    seg_femur_r = Segment(label='femur_r', imu_label='femur_r_imu',
                        parent=seg_tibia_r, length=25, initial_angle_deg=None)
    # seg_femur_l = Segment(label='femur_l', imu_label='femur_l_imu',
    #                       parent=seg_pelvis, length=33.5, initial_angle_deg=[-90,0,0],
    #                       parent_offset=np.array([5.0, 0.0, 10.0]))  # quadril esquerdo
    # seg_tibia_l = Segment(label='tibia_l', imu_label='tibia_l_imu',
    #                       parent=seg_femur_l, length=28.5, initial_angle_deg=[-90,0,0])
    # skeleton = [seg_pelvis, seg_femur_r, seg_tibia_r, seg_femur_l, seg_tibia_l]
    
    skeleton = [seg_tibia_r, seg_femur_r]

    df_angles_rel = calculate_joint_angles(skeleton, rotations, rot_seq=rot_seq)
    df_angles_rel.to_csv('angles.csv', index=False)
    print(df_angles_rel.head())

    df_angles_abs = calculate_global_angles(skeleton, rotations, rot_seq=rot_seq)
    df_angles_abs.to_csv('angles_abs.csv', index=False)
    print(df_angles_abs.head())

    # fig, ax = plt.subplots()
    # ax.plot(time, df_angles_rel['femur_r_y'])
    # ax.grid()
    # ax.set_aspect('equal')
    # plt.show()

    # fig, ax = plt.subplots()
    # ax.plot(time, df_angles_abs['tibia_r_x'], label='x')
    # ax.plot(time, df_angles_abs['tibia_r_y'], label='y')
    # ax.plot(time, df_angles_abs['tibia_r_z'], label='z')
    # ax.legend()
    # ax.grid()
    # plt.show()

    show_animation_arrows(skeleton, rotations, time, 1000 / resampling_rate,
                          rot_seq=rot_seq, trail_length=100)