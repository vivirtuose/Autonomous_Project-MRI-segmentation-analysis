"""
05_nnunet_inference.py
Inference nnU-Net sur les 4 modalites co-registrees.
Produit un masque de segmentation BraTS :
  label 0 = fond
  label 1 = necrose / tumeur non-rehaussante (NCR)
  label 2 = oedeme peritumoral (ED)
  label 3 = tumeur rehaussante (ET)

Prerequis :
  - nnU-Net installe (pip install nnunetv2)
  - Modele pre-entraine telecharge (nnUNet_results/)
  - 4 modalites co-registrees dans le dossier d'entree
    avec le nommage BraTS : _0000, _0001, _0002, _0003

NOTE : Ce script n'a pas encore ete execute dans le pipeline.
       Il est structure pour etre pret a l'emploi.
"""

import os
import subprocess
import sys
import shutil
import numpy as np
import nibabel as nib


def preparer_dossier_entree(coreg_dir, patient_id, nnunet_input_dir):
    """
    Prepare le dossier d'entree au format attendu par nnU-Net.
    nnU-Net attend un dossier contenant les 4 modalites nommees :
      PATIENT_0000.nii.gz  (T1CE)
      PATIENT_0001.nii.gz  (T1)
      PATIENT_0002.nii.gz  (T2)
      PATIENT_0003.nii.gz  (FLAIR)

    Args:
        coreg_dir (str): Dossier contenant les volumes co-registres
        patient_id (str): Identifiant du patient
        nnunet_input_dir (str): Dossier d'entree nnU-Net a creer
    """
    os.makedirs(nnunet_input_dir, exist_ok=True)

    # Correspondance fichier coreg -> fichier nnU-Net
    fichiers = {
        f'{patient_id}_0000_coreg.nii.gz': f'{patient_id}_0000.nii.gz',
        f'{patient_id}_0001_coreg.nii.gz': f'{patient_id}_0001.nii.gz',
        f'{patient_id}_0002_coreg.nii.gz': f'{patient_id}_0002.nii.gz',
        f'{patient_id}_0003_coreg.nii.gz': f'{patient_id}_0003.nii.gz',
    }

    for src_nom, dst_nom in fichiers.items():
        src = os.path.join(coreg_dir, src_nom)
        dst = os.path.join(nnunet_input_dir, dst_nom)

        if not os.path.exists(src):
            print(f"  MANQUANT : {src}")
            continue

        shutil.copy(src, dst)
        print(f"  {src_nom} -> {dst_nom}")

    print(f"\n  Dossier nnU-Net pret : {nnunet_input_dir}")


def lancer_inference_nnunet(nnunet_input_dir, nnunet_output_dir,
                             dataset_id='001', configuration='3d_fullres',
                             folds='all'):
    """
    Lance l'inference nnU-Net via la ligne de commande.

    Args:
        nnunet_input_dir (str): Dossier contenant les images d'entree
        nnunet_output_dir (str): Dossier de sortie pour les predictions
        dataset_id (str): Identifiant du dataset nnU-Net (ex: '001')
        configuration (str): Configuration du modele
                             ('3d_fullres' recommande pour IRM cerebrale)
        folds (str): Folds a utiliser ('all' pour le modele final)
    """
    os.makedirs(nnunet_output_dir, exist_ok=True)

    # Commande nnU-Net v2
    cmd = [
        'nnUNetv2_predict',
        '-i', nnunet_input_dir,      # dossier images d'entree
        '-o', nnunet_output_dir,      # dossier predictions de sortie
        '-d', dataset_id,             # identifiant du dataset
        '-c', configuration,          # configuration du modele
        *(['-f'] + folds.split()),    # folds utilises
        '--disable_tta',              # desactiver test-time augmentation
                                      # (plus rapide, legere perte de qualite)
    ]

    print(f"  Commande : {' '.join(cmd)}")
    print(f"  Inference en cours...")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"  Inference terminee -> {nnunet_output_dir}")
    else:
        print(f"  ERREUR lors de l'inference :")
        print(result.stderr)

    return result.returncode


def analyser_segmentation(chemin_masque):
    """
    Charge le masque de segmentation produit par nnU-Net
    et affiche les volumes tumoraux par compartiment BraTS.

    Convention BraTS :
      label 1 = NCR (necrose / tumeur non-rehaussante)
      label 2 = ED  (oedeme peritumoral)
      label 3 = ET  (tumeur rehaussante)

    Args:
        chemin_masque (str): Chemin vers le fichier .nii.gz de segmentation

    Returns:
        dict: Volumes en cm3 par compartiment
    """
    masque   = nib.load(chemin_masque)
    data_seg = masque.get_fdata().astype(int)

    # Volume d'un voxel en mm3
    voxel_vol_mm3 = np.prod(masque.header.get_zooms())

    labels_brats = {
        1: 'Necrose (NCR)',
        2: 'Oedeme (ED)',
        4: 'Tumeur rehaussante (ET)',
    }

    print(f"\n{'Compartiment':<30} {'N voxels':>10} {'Volume cm3':>10}")
    print('-' * 55)

    volumes = {}
    for label, nom in labels_brats.items():
        n   = np.sum(data_seg == label)
        vol = (n * voxel_vol_mm3) / 1000  # mm3 -> cm3
        volumes[nom] = vol
        print(f'{nom:<30} {n:>10} {vol:>10.2f}')

    # Volume total tumoral
    total_voxels = np.sum(data_seg > 0)
    total_cm3    = (total_voxels * voxel_vol_mm3) / 1000
    print(f'\n{"Volume total tumoral":<30} {total_voxels:>10} {total_cm3:>10.2f}')

    return volumes


# ============================================================
# EXECUTION
# ============================================================

if __name__ == '__main__':

    PATIENT_ID = 'UPENN-GBM-00283'
    DATA_DIR   = './data'
    COREG_DIR  = os.path.join(DATA_DIR, f'{PATIENT_ID}_coreg')

    NNUNET_INPUT  = os.path.join(DATA_DIR, f'{PATIENT_ID}_nnunet_input')
    NNUNET_OUTPUT = os.path.join(DATA_DIR, f'{PATIENT_ID}_nnunet_output')

    print(f"=== Inference nnU-Net pour {PATIENT_ID} ===\n")

    # Etape 1 : preparer le dossier d'entree
    print("--- Preparation du dossier d'entree ---")
    preparer_dossier_entree(COREG_DIR, PATIENT_ID, NNUNET_INPUT)

    # Etape 2 : lancer l'inference
    # DECOMMENTER quand nnU-Net est installe et le modele telecharge
    # print("\n--- Inference ---")
    # lancer_inference_nnunet(NNUNET_INPUT, NNUNET_OUTPUT)

    # Etape 3 : analyser le resultat
    # chemin_masque = os.path.join(NNUNET_OUTPUT, f'{PATIENT_ID}.nii.gz')
    # if os.path.exists(chemin_masque):
    #     print("\n--- Analyse de la segmentation ---")
    #     analyser_segmentation(chemin_masque)

    print("\nTermine.")
