"""
01_download_dicom.py
Telechargement des series DICOM depuis TCIA (collection UPENN-GBM).
Telecharge les 4 modalites necessaires au pipeline BraTS :
T1, T1CE (3D GAD), T2, FLAIR.
"""

import os
import pandas as pd
from tcia_utils import nbia


def lister_series(collection):
    """
    Recupere toutes les series disponibles pour une collection TCIA.

    Args:
        collection (str): Nom de la collection TCIA (ex: 'UPENN-GBM')

    Returns:
        pd.DataFrame: DataFrame avec les colonnes PatientID,
                       SeriesDescription, FileSize, SeriesInstanceUID, etc.
    """
    series_df = pd.DataFrame(nbia.getSeries(collection=collection))
    return series_df


def lister_patients(series_df):
    """
    Affiche la liste des patients disponibles dans le DataFrame de series.

    Args:
        series_df (pd.DataFrame): DataFrame retourne par lister_series()
    """
    patients = series_df['PatientID'].unique()
    print(f"Patients disponibles : {len(patients)}")
    print(patients[:10], "...")
    return patients


def afficher_series_patient(series_df, patient_id):
    """
    Affiche toutes les series disponibles pour un patient donne.

    Args:
        series_df (pd.DataFrame): DataFrame des series
        patient_id (str): Identifiant du patient (ex: 'UPENN-GBM-00283')
    """
    series_patient = series_df[series_df['PatientID'] == patient_id]
    print(f"\nSeries disponibles pour {patient_id} :")
    print(series_patient[['SeriesDescription', 'FileSize']].to_string())
    return series_patient


def telecharger_serie(series_df, patient_id, filtre_description, dossier_sortie):
    """
    Telecharge une serie DICOM specifique depuis TCIA.

    Args:
        series_df (pd.DataFrame): DataFrame des series
        patient_id (str): Identifiant du patient
        filtre_description (str): Texte a chercher dans SeriesDescription
                                  (ex: '3D GAD', 'T2', 'FLAIR')
        dossier_sortie (str): Chemin du dossier de destination

    Returns:
        bool: True si le telechargement a reussi, False sinon
    """
    series_patient = series_df[series_df['PatientID'] == patient_id]

    serie = series_patient[
        series_patient['SeriesDescription'].str.contains(
            filtre_description, case=False, na=False
        )
    ]

    if len(serie) == 0:
        print(f"  Pas de serie '{filtre_description}' pour {patient_id}")
        return False

    if os.path.exists(dossier_sortie):
        print(f"  Deja telecharge : {dossier_sortie}")
        return True

    uid = serie['SeriesInstanceUID'].iloc[0]
    taille_mb = serie['FileSize'].iloc[0] / (1024**2)
    print(f"  Serie   : {serie['SeriesDescription'].iloc[0]}")
    print(f"  Taille  : {taille_mb:.1f} MB")

    nbia.downloadSeries([uid], input_type="list", path=dossier_sortie)
    print(f"  Telecharge -> {dossier_sortie}")
    return True


def telecharger_4_modalites(series_df, patient_id, data_dir='./data'):
    """
    Telecharge les 4 modalites BraTS pour un patient :
    T1 (standard), T1CE (3D GAD), T2, FLAIR.

    Args:
        series_df (pd.DataFrame): DataFrame des series
        patient_id (str): Identifiant du patient
        data_dir (str): Dossier racine de stockage (defaut: './data')
    """
    os.makedirs(data_dir, exist_ok=True)

    # Modalites a telecharger et leur filtre de recherche
    modalites = {
        '3D GAD': f'{data_dir}/{patient_id}_3DGAD',   # T1CE
        'T2':     f'{data_dir}/{patient_id}_T2',       # T2
        'FLAIR':  f'{data_dir}/{patient_id}_FLAIR',    # FLAIR
    }

    # T1 standard (premiere serie du patient, sans filtre specifique)
    dossier_t1 = f'{data_dir}/{patient_id}'
    if not os.path.exists(dossier_t1):
        series_patient = series_df[series_df['PatientID'] == patient_id]
        uid = series_patient['SeriesInstanceUID'].iloc[0]
        nbia.downloadSeries([uid], input_type="list", path=dossier_t1)
        print(f"  T1 telecharge -> {dossier_t1}")
    else:
        print(f"  T1 deja present : {dossier_t1}")

    for filtre, dossier in modalites.items():
        print(f"\n--- {filtre} ---")
        telecharger_serie(series_df, patient_id, filtre, dossier)


# ============================================================
# EXECUTION
# ============================================================

if __name__ == '__main__':

    COLLECTION = 'UPENN-GBM'         # collection TCIA cible
    PATIENT_ID = 'UPENN-GBM-00283'   # patient a telecharger
    DATA_DIR   = './data'

    print("=== Recuperation des series TCIA ===")
    series_df = lister_series(COLLECTION)
    lister_patients(series_df)

    print(f"\n=== Telechargement des 4 modalites pour {PATIENT_ID} ===")
    telecharger_4_modalites(series_df, PATIENT_ID, DATA_DIR)

    print("\nTermine.")
