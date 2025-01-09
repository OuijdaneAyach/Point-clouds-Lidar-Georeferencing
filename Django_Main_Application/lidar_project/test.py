import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def plot_nuage_3d(fichier_txt):
    """
    Lit un fichier .txt contenant les colonnes x, y, z et trace le nuage de points en 3D.

    Args:
        fichier_txt (str): Chemin vers le fichier .txt contenant les données x, y, z.
    """
    try:
        # Charger les données
        points = np.loadtxt(fichier_txt)

        # Vérifier si le fichier a 3 colonnes
        if points.shape[1] != 3:
            print("Erreur : Le fichier doit contenir exactement 3 colonnes : x, y, z.")
            return

        # Séparer les coordonnées x, y, z
        x, y, z = points[:, 0], points[:, 1], points[:, 2]

        # Initialiser le plot 3D
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')

        # Tracer les points
        ax.scatter(x, y, z, c='blue', s=1)  # 's' contrôle la taille des points

        # Ajouter des étiquettes et titre
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.title('Nuage de Points 3D')

        # Afficher
        plt.show()
    except Exception as e:
        print(f"Erreur lors de la lecture ou du tracé : {e}")


# Exemple d'utilisation
fichier = r"C:\Users\ayach\Downloads\georeferenced_data (3).txt"  # Remplacez par le chemin de votre fichier
plot_nuage_3d(fichier)
