"""
03_visualize_nifti.py
Visualisation interactive de volumes NIFTI :
  - 3 plans anatomiques (axial, sagittal, coronal)
  - Correction du ratio d'aspect pour volumes anisotropiques
  - Slider interactif pour naviguer dans les coupes
"""

import os
import json
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


def afficher_info_nifti(chemin_nifti):
    """
    Charge un fichier NIFTI et affiche ses metadonnees principales :
    shape, taille des voxels, type de donnees, min/max, matrice affine.

    Args:
        chemin_nifti (str): Chemin vers le fichier .nii.gz

    Returns:
        tuple: (objet nibabel image, numpy array des donnees)
    """
    img  = nib.load(chemin_nifti)
    data = img.get_fdata()

    print('=== HEADER NIFTI ===')
    print(f'Shape          : {data.shape}')
    print(f'Taille voxels  : {img.header.get_zooms()} mm')
    print(f'Type donnees   : {data.dtype}')
    print(f'Min / Max      : {data.min():.1f} / {data.max():.1f}')
    print(f'\nMatrice affine :\n{img.affine}')

    return img, data


def afficher_sidecar_json(chemin_json):
    """
    Affiche les metadonnees BIDS contenues dans le fichier sidecar JSON
    produit par dcm2niix lors de la conversion DICOM -> NIFTI.

    Args:
        chemin_json (str): Chemin vers le fichier .json sidecar
    """
    if not os.path.exists(chemin_json):
        print(f"Sidecar JSON non trouve : {chemin_json}")
        return

    with open(chemin_json) as f:
        meta = json.load(f)

    champs_utiles = [
        'Modality', 'MagneticFieldStrength', 'RepetitionTime',
        'EchoTime', 'SliceThickness', 'Manufacturer'
    ]
    print('\n=== METADONNEES BIDS (sidecar JSON) ===')
    for champ in champs_utiles:
        if champ in meta:
            print(f'{champ:25} : {meta[champ]}')


def visualiser_3_plans(data, zooms=None, titre='IRM'):
    """
    Affiche les 3 plans anatomiques (axial, coronal, sagittal)
    au centre du volume, avec correction du ratio d'aspect
    si le volume est anisotropique.

    Args:
        data (np.ndarray): Volume 3D (X, Y, Z)
        zooms (tuple): Taille des voxels (px, py, pz) en mm.
                       Si fourni, corrige le ratio d'aspect
                       des vues coronale et sagittale.
        titre (str): Titre de la figure
    """
    cx, cy, cz = [s // 2 for s in data.shape[:3]]

    # Ratio d'aspect pour corriger l'anisotropie
    # En vue axiale (plan XY), les voxels sont carres -> aspect=1
    # En vue coronale/sagittale, l'axe Z peut avoir un espacement different
    if zooms is not None:
        ratio = zooms[2] / zooms[0]  # espacement Z / espacement XY
    else:
        ratio = 1

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(titre, fontsize=14, fontweight='bold')

    # Axiale : coupe dans le plan XY a z=cz
    axes[0].imshow(data[:, :, cz].T, cmap='gray', origin='lower')
    axes[0].set_title(f'Axiale (z={cz})')
    axes[0].axis('off')

    # Coronale : coupe dans le plan XZ a y=cy
    axes[1].imshow(data[:, cy, :].T, cmap='gray', origin='lower',
                   aspect=ratio)
    axes[1].set_title(f'Coronale (y={cy})')
    axes[1].axis('off')

    # Sagittale : coupe dans le plan YZ a x=cx
    axes[2].imshow(data[cx, :, :].T, cmap='gray', origin='lower',
                   aspect=ratio)
    axes[2].set_title(f'Sagittale (x={cx})')
    axes[2].axis('off')

    plt.tight_layout()
    plt.show()


def visualiser_interactif(data, zooms=None, titre='IRM'):
    """
    Affiche un visualiseur interactif avec sliders pour naviguer
    dans les 3 plans anatomiques.

    Args:
        data (np.ndarray): Volume 3D (X, Y, Z)
        zooms (tuple): Taille des voxels (px, py, pz) en mm
        titre (str): Titre de la figure
    """
    if zooms is not None:
        ratio = zooms[2] / zooms[0]
    else:
        ratio = 1

    nx, ny, nz = data.shape

    fig, axes = plt.subplots(1, 3, figsize=(15, 6))
    fig.suptitle(titre, fontsize=14, fontweight='bold')
    plt.subplots_adjust(bottom=0.2)

    def afficher(cx, cy, cz):
        """Met a jour les 3 plans pour les indices donnes."""
        cx, cy, cz = int(cx), int(cy), int(cz)

        axes[0].cla()
        axes[0].imshow(data[:, :, cz].T, cmap='gray', origin='lower')
        axes[0].set_title(f'Axiale z={cz}')
        axes[0].axis('off')

        axes[1].cla()
        axes[1].imshow(data[cx, :, :].T, cmap='gray', origin='lower',
                       aspect=ratio)
        axes[1].set_title(f'Sagittale x={cx}')
        axes[1].axis('off')

        axes[2].cla()
        axes[2].imshow(data[:, cy, :].T, cmap='gray', origin='lower',
                       aspect=ratio)
        axes[2].set_title(f'Coronale y={cy}')
        axes[2].axis('off')

        fig.canvas.draw_idle()

    # Affichage initial au centre du volume
    afficher(nx // 2, ny // 2, nz // 2)

    # Sliders
    ax_z = plt.axes([0.15, 0.12, 0.7, 0.025])
    ax_x = plt.axes([0.15, 0.08, 0.7, 0.025])
    ax_y = plt.axes([0.15, 0.04, 0.7, 0.025])

    slider_z = Slider(ax_z, 'Axiale (Z)',    0, nz - 1,
                      valinit=nz // 2, valstep=1)
    slider_x = Slider(ax_x, 'Sagittale (X)', 0, nx - 1,
                      valinit=nx // 2, valstep=1)
    slider_y = Slider(ax_y, 'Coronale (Y)',  0, ny - 1,
                      valinit=ny // 2, valstep=1)

    def update(val):
        afficher(slider_x.val, slider_y.val, slider_z.val)

    slider_z.on_changed(update)
    slider_x.on_changed(update)
    slider_y.on_changed(update)

    plt.show()


# ============================================================
# EXECUTION
# ============================================================

if __name__ == '__main__':

    PATIENT_ID = 'UPENN-GBM-00283'
    DATA_DIR   = './data'
    NIFTI_DIR  = os.path.join(DATA_DIR, f'{PATIENT_ID}_4mod_nifti')

    # Fichier T1CE (3D GAD, haute resolution)
    chemin_nifti = os.path.join(NIFTI_DIR, f'{PATIENT_ID}_0000.nii.gz')
    chemin_json  = os.path.join(NIFTI_DIR, f'{PATIENT_ID}_0000.json')

    print(f"=== Visualisation de {chemin_nifti} ===")
    img, data = afficher_info_nifti(chemin_nifti)
    afficher_sidecar_json(chemin_json)

    zooms = img.header.get_zooms()
    visualiser_3_plans(data, zooms, titre=f'IRM T1CE -- {PATIENT_ID}')
    visualiser_interactif(data, zooms, titre=f'IRM T1CE -- {PATIENT_ID}')






def visualiser_segmentation(data, data_seg, zooms=None, titre='Segmentation'):
    """
    Affiche l'IRM originale avec le masque de segmentation superpose.
    Slider interactif pour naviguer dans les coupes axiales.

    Args:
        data (np.ndarray): Volume IRM 3D (X, Y, Z)
        data_seg (np.ndarray): Masque de segmentation (X, Y, Z)
                               Labels BraTS : 0=fond, 1=NCR, 2=ED, 4=ET
        zooms (tuple): Taille des voxels (px, py, pz) en mm
        titre (str): Titre de la figure
    """
    if zooms is not None:
        ratio = zooms[2] / zooms[0]
    else:
        ratio = 1

    nx, ny, nz = data.shape

    # Colormap : associe chaque label a une couleur
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    # Labels BraTS : 0=fond(transparent), 1=NCR(rouge), 2=ED(jaune), 4=ET(bleu)
    # On cree une colormap indexee de 0 a 4
    couleurs_rgba = [
        (0, 0, 0, 0),        # 0 = fond (transparent)
        (1, 0, 0, 0.6),      # 1 = NCR (rouge)
        (1, 1, 0, 0.6),      # 2 = ED (jaune)
        (0, 0, 0, 0),        # 3 = inutilise
        (0, 0.4, 1, 0.6),    # 4 = ET (bleu)
    ]
    cmap_seg = ListedColormap(couleurs_rgba)

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(titre, fontsize=14, fontweight='bold')
    plt.subplots_adjust(bottom=0.15, hspace=0.3)

    def afficher(cx, cy, cz):
        """Met a jour les 6 panneaux."""
        cx, cy, cz = int(cx), int(cy), int(cz)

        # Ligne du haut : IRM seule
        axes[0, 0].cla()
        axes[0, 0].imshow(data[:, :, cz].T, cmap='gray', origin='lower')
        axes[0, 0].set_title(f'Axiale z={cz}')
        axes[0, 0].axis('off')

        axes[0, 1].cla()
        axes[0, 1].imshow(data[cx, :, :].T, cmap='gray', origin='lower',
                          aspect=ratio)
        axes[0, 1].set_title(f'Sagittale x={cx}')
        axes[0, 1].axis('off')

        axes[0, 2].cla()
        axes[0, 2].imshow(data[:, cy, :].T, cmap='gray', origin='lower',
                          aspect=ratio)
        axes[0, 2].set_title(f'Coronale y={cy}')
        axes[0, 2].axis('off')

        # Ligne du bas : IRM + segmentation superposee
        for col, (coupe_img, coupe_seg, asp) in enumerate([
            (data[:, :, cz].T,  data_seg[:, :, cz].T,  1),
            (data[cx, :, :].T,  data_seg[cx, :, :].T,  ratio),
            (data[:, cy, :].T,  data_seg[:, cy, :].T,  ratio),
        ]):
            axes[1, col].cla()
            axes[1, col].imshow(coupe_img, cmap='gray', origin='lower',
                                aspect=asp)
            # Masquer le fond (label 0) pour ne superposer que la tumeur
            seg_masque = np.ma.masked_where(coupe_seg == 0, coupe_seg)
            axes[1, col].imshow(seg_masque, cmap=cmap_seg, origin='lower',
                                aspect=asp, vmin=0, vmax=4)
            axes[1, col].axis('off')

        axes[1, 0].set_title('Axiale + segmentation')
        axes[1, 1].set_title('Sagittale + segmentation')
        axes[1, 2].set_title('Coronale + segmentation')

        # Legende
        legende = [
            Patch(color=(1, 0, 0, 0.6),    label='NCR (necrose)'),
            Patch(color=(1, 1, 0, 0.6),    label='ED (oedeme)'),
            Patch(color=(0, 0.4, 1, 0.6),  label='ET (rehaussante)'),
        ]
        axes[1, 2].legend(handles=legende, loc='lower right', fontsize=8)

        fig.canvas.draw_idle()

    # Trouver la coupe avec le plus de tumeur pour l'affichage initial
    tumeur_par_coupe = np.sum(data_seg > 0, axis=(0, 1))
    cz_init = int(np.argmax(tumeur_par_coupe))

    afficher(nx // 2, ny // 2, cz_init)

    # Sliders
    ax_z = plt.axes([0.15, 0.08, 0.7, 0.025])
    ax_x = plt.axes([0.15, 0.04, 0.7, 0.025])
    ax_y = plt.axes([0.15, 0.00, 0.7, 0.025])

    slider_z = Slider(ax_z, 'Axiale (Z)',    0, nz - 1,
                      valinit=cz_init, valstep=1)
    slider_x = Slider(ax_x, 'Sagittale (X)', 0, nx - 1,
                      valinit=nx // 2, valstep=1)
    slider_y = Slider(ax_y, 'Coronale (Y)',  0, ny - 1,
                      valinit=ny // 2, valstep=1)

    def update(val):
        afficher(slider_x.val, slider_y.val, slider_z.val)

    slider_z.on_changed(update)
    slider_x.on_changed(update)
    slider_y.on_changed(update)

    plt.show()