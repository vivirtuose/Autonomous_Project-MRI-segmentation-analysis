"""
02_convert_dicom_to_nifti.py
Conversion des dossiers DICOM en fichiers NIFTI (.nii.gz)
via dcm2niix, avec nommage standardise BraTS :
  _0000 = T1CE (3D GAD)
  _0001 = T1
  _0002 = T2
  _0003 = FLAIR
"""

import os
import subprocess


def trouver_sous_dossier_dicom(chemin_dossier):
    """
    Trouve le sous-dossier SeriesUID a l'interieur d'un dossier
    telecharge par TCIA. La structure typique est :
    ./data/PATIENT_MODALITE/SeriesUID_long/fichiers.dcm

    Args:
        chemin_dossier (str): Chemin vers le dossier parent

    Returns:
        str: Chemin vers le sous-dossier contenant les .dcm
    """
    sous_dossiers = [
        d for d in os.listdir(chemin_dossier)
        if os.path.isdir(os.path.join(chemin_dossier, d))
    ]
    if not sous_dossiers:
        raise FileNotFoundError(
            f"Aucun sous-dossier dans {chemin_dossier}"
        )
    return os.path.join(chemin_dossier, sous_dossiers[0])


def convertir_dicom_vers_nifti(dossier_dicom, output_dir, nom_sortie,
                                dcm2niix_exe='dcm2niix'):
    """
    Convertit un dossier DICOM en fichier NIFTI compresse (.nii.gz)
    via dcm2niix.

    Args:
        dossier_dicom (str): Chemin du dossier contenant les .dcm
        output_dir (str): Dossier de sortie pour le .nii.gz
        nom_sortie (str): Nom du fichier de sortie (sans extension)
        dcm2niix_exe (str): Chemin vers l'executable dcm2niix
                            (defaut: 'dcm2niix', suppose dans le PATH)
                            Sur Windows: './dcm2niix.exe'
    """
    nifti_existant = os.path.join(output_dir, f'{nom_sortie}.nii.gz')
    if os.path.exists(nifti_existant):
        print(f"  {nom_sortie} -- deja converti")
        return

    print(f"  Conversion -> {nom_sortie}.nii.gz")
    subprocess.run([
        dcm2niix_exe,
        '-o', output_dir,  # dossier de sortie
        '-z', 'y',         # compression gzip activee
        '-f', nom_sortie,  # format du nom de fichier
        dossier_dicom
    ], capture_output=True)
    print(f"  {nom_sortie} converti")


def convertir_4_modalites(patient_id, data_dir='./data',
                           dcm2niix_exe='dcm2niix'):
    """
    Convertit les 4 modalites DICOM d'un patient en NIFTI
    avec le nommage BraTS standardise.

    Convention BraTS :
      _0000 = T1CE (contraste gadolinium, serie 3D GAD)
      _0001 = T1   (sans contraste)
      _0002 = T2
      _0003 = FLAIR

    Args:
        patient_id (str): Identifiant du patient (ex: 'UPENN-GBM-00283')
        data_dir (str): Dossier racine des donnees
        dcm2niix_exe (str): Chemin vers l'executable dcm2niix
    """
    # Correspondance dossier DICOM -> suffixe BraTS
    modalites = {
        f'{patient_id}_3DGAD': f'{patient_id}_0000',  # T1CE
        f'{patient_id}':       f'{patient_id}_0001',  # T1
        f'{patient_id}_T2':    f'{patient_id}_0002',  # T2
        f'{patient_id}_FLAIR': f'{patient_id}_0003',  # FLAIR
    }

    output_dir = os.path.join(data_dir, f'{patient_id}_4mod_nifti')
    os.makedirs(output_dir, exist_ok=True)

    for dossier_dicom_nom, nom_sortie in modalites.items():
        chemin_dicom = os.path.join(data_dir, dossier_dicom_nom)

        if not os.path.exists(chemin_dicom):
            print(f"  Dossier manquant : {chemin_dicom}")
            continue

        dossier_dcm = trouver_sous_dossier_dicom(chemin_dicom)
        convertir_dicom_vers_nifti(
            dossier_dcm, output_dir, nom_sortie, dcm2niix_exe
        )

    # Verification finale
    print(f"\n=== Fichiers NIFTI produits ===")
    for f in sorted(os.listdir(output_dir)):
        if f.endswith('.nii.gz'):
            taille = os.path.getsize(os.path.join(output_dir, f)) / (1024**2)
            print(f"  {f} ({taille:.1f} MB)")

    return output_dir


# ============================================================
# EXECUTION
# ============================================================

if __name__ == '__main__':

    PATIENT_ID   = 'UPENN-GBM-00283'
    DATA_DIR     = './data'
    DCM2NIIX_EXE = './dcm2niix.exe'  # adapter selon l'OS

    print(f"=== Conversion DICOM -> NIFTI pour {PATIENT_ID} ===")
    output_dir = convertir_4_modalites(
        PATIENT_ID, DATA_DIR, DCM2NIIX_EXE
    )

    print("\nTermine.")
