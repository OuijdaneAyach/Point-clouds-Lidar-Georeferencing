from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt


UPLOAD_FOLDER = os.path.join(settings.BASE_DIR, 'uploads')
RESULTS_FOLDER = os.path.join(settings.BASE_DIR, 'results')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)


lidar_points = []
georeferenced_points = []


def compute_rotation_matrix(roll, pitch, heading):
    roll, pitch, heading = np.radians([roll, pitch, heading])
    R_roll = np.array([[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]])
    R_pitch = np.array([[np.cos(pitch), 0, np.sin(pitch)], [0, 1, 0], [-np.sin(pitch), 0, np.cos(pitch)]])
    R_heading = np.array([[np.cos(heading), -np.sin(heading), 0], [np.sin(heading), np.cos(heading), 0], [0, 0, 1]])
    return R_heading @ R_pitch @ R_roll


def transform_lidar(points, R_imu, T_gps, lever_arm, R_imu_to_scanner):
    transformed_points = []
    for point in points:
        local_point = np.array(point)
        transformed_point = T_gps + R_imu @ (lever_arm + R_imu_to_scanner @ local_point)
        transformed_points.append(transformed_point)
    return np.array(transformed_points)


def save_results(data, file_name):
    result_path = os.path.join(RESULTS_FOLDER, file_name)
    np.savetxt(result_path, data, fmt='%.6f', delimiter=' ')
    return result_path


def download_results(request, file_name):
    file_path = os.path.join(RESULTS_FOLDER, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="text/plain")
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    return HttpResponse("File not found.", status=404)

def save_results(data, file_name):
    result_path = os.path.join(RESULTS_FOLDER, file_name)
    np.savetxt(result_path, data, fmt='%.6f', delimiter=' ')
    return result_path


def save_graph(points, file_name):
    """
    Fonction pour sauvegarder un graphe 3D géoréférencé avec une barre de couleur et un affichage optimisé.
    """
    fig = plt.figure(figsize=(16, 10))  # Taille augmentée pour occuper toute la fenêtre
    ax = fig.add_subplot(111, projection='3d')

    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    scatter = ax.scatter(x, y, z, c=z, cmap='viridis', marker='o', s=2)  # Points colorés par Z

    colorbar = fig.colorbar(scatter, ax=ax, pad=0.2, aspect=20, shrink=0.8)
    colorbar.set_label('Z Axis (Color Scale)', fontsize=12)

    xticks = np.linspace(min(x), max(x), 4)  # 4 valeurs sur l'axe X
    yticks = np.linspace(min(y), max(y), 4)  # 4 valeurs sur l'axe Y
    zticks = np.linspace(min(z), max(z), 4)  # 4 valeurs sur l'axe Z

    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    ax.set_zticks(zticks)

    ax.set_title("3D Georeferenced Graph", fontsize=20, pad=20)
    ax.set_xlabel("X Axis", fontsize=14, labelpad=10)
    ax.set_ylabel("Y Axis", fontsize=14, labelpad=10)
    ax.set_zlabel("Z Axis", fontsize=14, labelpad=10)

    ax.set_xticklabels([f"{tick:.1f}" for tick in xticks], fontsize=10)
    ax.set_yticklabels([f"{tick:.1f}" for tick in yticks], fontsize=10)
    ax.set_zticklabels([f"{tick:.1f}" for tick in zticks], fontsize=10)

    plt.tight_layout()

    file_path = os.path.join(RESULTS_FOLDER, file_name)
    plt.savefig(file_path, dpi=300, bbox_inches='tight')
    plt.close(fig)


def download_graph(request):
    file_name = 'georeferenced_graph_3d.png'
    file_path = os.path.join(RESULTS_FOLDER, file_name)

    if not os.path.exists(file_path):
        if georeferenced_points:
            save_graph(np.vstack(georeferenced_points), file_name)
        else:
            return HttpResponse("No georeferenced points available to generate the graph.", status=400)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="image/png")
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    return HttpResponse("Graph file not found.", status=404)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="image/png")
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response

    return HttpResponse("Graph file not found.", status=404)


def download_results(request):
    file_name = 'georeferenced_data.txt'
    file_path = os.path.join(RESULTS_FOLDER, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="text/plain")
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    return HttpResponse("File not found.", status=404)

def download_graph(request):
    file_name = 'georeferenced_graph_3d.png'
    file_path = os.path.join(RESULTS_FOLDER, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="image/png")
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    return HttpResponse("Graph file not found.", status=404)

def index(request):
    global lidar_points, georeferenced_points
    plot_html = None
    georeferenced_plot_html = None

    if request.method == 'POST':
        # Upload LiDAR files
        if 'files[]' in request.FILES:
            uploaded_files = request.FILES.getlist('files[]')
            lidar_points = []
            file_names = []

            for file in uploaded_files:
                if file.name.endswith('.xyz'):
                    filepath = os.path.join(UPLOAD_FOLDER, file.name)
                    with open(filepath, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)

                    try:
                        # Lecture des données LiDAR
                        data = pd.read_csv(filepath, sep=r'\s+', header=None)
                        if data.shape[1] < 5:
                            return render(request, 'lidar/index.html', {'error': f"File {file.name} does not have enough columns."})

                        # Extraire les colonnes X, Y, Z
                        data = data.iloc[:, [2, 3, 4]]
                        data.columns = ['X', 'Y', 'Z']

                        # Échantillonner si nécessaire
                        if len(data) > 10000:
                            data = data.sample(10000)

                        lidar_points.append(data.values)
                        file_names.append(file.name)
                    except Exception as e:
                        return render(request, 'lidar/index.html', {'error': f"Error processing file {file.name}: {str(e)}"})

            if lidar_points:
                traces = []
                for points, file_name in zip(lidar_points, file_names):
                    trace = go.Scatter3d(
                        x=points[:, 0], y=points[:, 1], z=points[:, 2],
                        mode='markers',
                        marker=dict(size=2, color=points[:, 2], colorscale='Viridis', opacity=0.8),
                        name=file_name
                    )
                    traces.append(trace)

                layout = go.Layout(
                    title="3D LiDAR Visualization",
                    scene=dict(
                        xaxis=dict(title="X-axis"),
                        yaxis=dict(title="Y-axis"),
                        zaxis=dict(title="Z-axis"),
                    ),
                    margin=dict(l=0, r=0, b=0, t=40),
                    height=500,
                    width=1200,
                )

                fig = go.Figure(data=traces, layout=layout)
                plot_html = fig.to_html(full_html=False)

        elif 'gps_file' in request.FILES:
            gps_file = request.FILES['gps_file']
            gps_path = os.path.join(UPLOAD_FOLDER, gps_file.name)
            with open(gps_path, 'wb+') as destination:
                for chunk in gps_file.chunks():
                    destination.write(chunk)

            try:
                # Lecture des données GPS
                gps_data = pd.read_csv(gps_path, sep='\t', header=0)
                if gps_data.shape[1] < 10:
                    return render(request, 'lidar/index.html', {'error': "Invalid GPS file format."})

                # Calcul des matrices de transformation
                R_imu = compute_rotation_matrix(gps_data['Roll'][0], gps_data['Pitch'][0], gps_data['Heading'][0])
                T_gps = np.array([gps_data['X'][0], gps_data['Y'][0], gps_data['Z'][0]])

                lever_arm = np.array([0.14, 0.249, -0.076])
                R_imu_to_scanner = np.eye(3)

                if not lidar_points:
                    return render(request, 'lidar/index.html', {'error': "No LiDAR data uploaded for georeferencing."})

                georeferenced_points = []
                for points in lidar_points:
                    transformed_points = transform_lidar(points, R_imu, T_gps, lever_arm, R_imu_to_scanner)
                    georeferenced_points.append(transformed_points)

                georeferenced_traces = []
                for points in georeferenced_points:
                    trace = go.Scatter3d(
                        x=points[:, 0], y=points[:, 1], z=points[:, 2],
                        mode='markers',
                        marker=dict(size=2, color=points[:, 2], colorscale='Viridis', opacity=0.8),
                        name="Georeferenced LiDAR"
                    )
                    georeferenced_traces.append(trace)

                layout = go.Layout(
                    title="3D Georeferenced LiDAR Visualization",
                    scene=dict(
                        xaxis=dict(title="X-axis"),
                        yaxis=dict(title="Y-axis"),
                        zaxis=dict(title="Z-axis"),
                    ),
                    margin=dict(l=0, r=0, b=0, t=40),
                    height=500,
                    width=1200,
                )

                fig = go.Figure(data=georeferenced_traces, layout=layout)
                georeferenced_plot_html = fig.to_html(full_html=False)

                # Save georeferenced data and graph
                save_results(np.vstack(georeferenced_points), 'georeferenced_data.txt')
                save_graph(np.vstack(georeferenced_points), 'georeferenced_graph_3d.png')

            except Exception as e:
                return render(request, 'lidar/index.html', {'error': f"Error processing GPS file: {str(e)}"})

    return render(request, 'lidar/index.html', {
        'plot_html': plot_html,
        'georeferenced_plot_html': georeferenced_plot_html
    })
