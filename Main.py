"""
Main.py
Pipeline complet de segmentation d'IRM cerebrales.
Orchestre les 5 etapes du projet :
  01 - Telechargement des series DICOM depuis TCIA
  02 - Conversion DICOM -> NIFTI (dcm2niix)
  03 - Visualisation des volumes NIFTI
  04 - Co-registration des 4 modalites (ANTs)
  05 - Inference nnU-Net (segmentation tumorale BraTS)

Chaque etape peut etre executee independamment via son script,
ou orchestree ici en sequence.
"""

import os
import importlib

# ============================================================
# CONFIGURATION GLOBALE
# ============================================================

PATIENT_ID   = 'UPENN-GBM-00283'   # patient cible
COLLECTION   = 'UPENN-GBM'         # collection TCIA
DATA_DIR     = './data'             # dossier racine des donnees
DCM2NIIX_EXE = './dcm2niix.exe'    # chemin dcm2niix (adapter selon l'OS)

# Dossiers derives (calcules automatiquement)
NIFTI_DIR      = os.path.join(DATA_DIR, f'{PATIENT_ID}_4mod_nifti')
COREG_DIR      = os.path.join(DATA_DIR, f'{PATIENT_ID}_coreg')
NNUNET_INPUT   = os.path.join(DATA_DIR, f'{PATIENT_ID}_nnunet_input')
NNUNET_OUTPUT  = os.path.join(DATA_DIR, f'{PATIENT_ID}_nnunet_output')

# ============================================================
# SELECTION DES ETAPES A EXECUTER
# Mettre True/False pour activer/desactiver chaque etape
# ============================================================

EXECUTER = {
    '01_download':     False,  #False tant que le telechargement n'est pas au point ou déja fait
    '02_convert':      False,  #False tant que la conversion n'est pas au point ou déja faite
    '03_visualize':    False,  #False tant que la visualisation n'est pas au point ou déja faite
    '04_coregister':   False,  # False tant que la coregistration n'est pas au point ou déja fait
    '05_nnunet':       True,  # False tant que nnU-Net n'est pas installe
}


# ============================================================
# EXECUTION DU PIPELINE
# ============================================================

if __name__ == '__main__':

    # --- 01 : Telechargement DICOM ---
    if EXECUTER['01_download']:
        print('\n' + '=' * 60)
        print('ETAPE 01 : Telechargement des series DICOM')
        print('=' * 60)

        mod01 = importlib.import_module('01_download_dicom')
        series_df = mod01.lister_series(COLLECTION)
        mod01.telecharger_4_modalites(series_df, PATIENT_ID, DATA_DIR)

    # --- 02 : Conversion DICOM -> NIFTI ---
    if EXECUTER['02_convert']:
        print('\n' + '=' * 60)
        print('ETAPE 02 : Conversion DICOM -> NIFTI')
        print('=' * 60)

        mod02 = importlib.import_module('02_convert_dicom_to_nifti')
        mod02.convertir_4_modalites(PATIENT_ID, DATA_DIR, DCM2NIIX_EXE)

    # --- 03 : Visualisation ---
    if EXECUTER['03_visualize']:
        print('\n' + '=' * 60)
        print('ETAPE 03 : Visualisation NIFTI')
        print('=' * 60)

        mod03 = importlib.import_module('03_visualize_nifti')
        chemin = os.path.join(NIFTI_DIR, f'{PATIENT_ID}_0000.nii.gz')
        img, data = mod03.afficher_info_nifti(chemin)
        zooms = img.header.get_zooms()
        mod03.visualiser_interactif(data, zooms, titre=f'T1CE -- {PATIENT_ID}')

    # --- 04 : Co-registration ---
    if EXECUTER['04_coregister']:
        print('\n' + '=' * 60)
        print('ETAPE 04 : Co-registration des 4 modalites')
        print('=' * 60)

        mod04 = importlib.import_module('04_coregistration')
        mod04.verifier_volumes(NIFTI_DIR, PATIENT_ID)
        mod04.coregistrer_modalites(NIFTI_DIR, COREG_DIR, PATIENT_ID)
        mod04.verifier_coregistration(COREG_DIR)

# --- 05 : Inference nnU-Net ---
    if EXECUTER['05_nnunet']:
        print('\n' + '=' * 60)
        print('ETAPE 05 : Inference nnU-Net')
        print('=' * 60)

        mod05 = importlib.import_module('05_nnunet_inference')
        mod05.preparer_dossier_entree(COREG_DIR, PATIENT_ID, NNUNET_INPUT)
        mod05.lancer_inference_nnunet(
            NNUNET_INPUT, NNUNET_OUTPUT,
            dataset_id='002',           # Dataset002_BRATS19
            configuration='3d_fullres',   # configuration 3D pleine resolution
            folds='0 1 2 3 4'
        )

        chemin_masque = os.path.join(
            NNUNET_OUTPUT, f'{PATIENT_ID}.nii.gz'
        )
        if os.path.exists(chemin_masque):
            mod05.analyser_segmentation(chemin_masque)

    print('\n' + '=' * 60)
    print('Pipeline termine.')
    print('=' * 60)


if os.path.exists(chemin_masque):
            mod05.analyser_segmentation(chemin_masque)

            # Visualisation segmentation sur IRM
            mod03 = importlib.import_module('03_visualize_nifti')
            import nibabel as nib
            import numpy as np

            # Charger le T1CE (reference) et le masque de segmentation
            img_ref = nib.load(os.path.join(NNUNET_INPUT, f'{PATIENT_ID}_0000.nii.gz'))
            data_ref = img_ref.get_fdata()
            data_seg = nib.load(chemin_masque).get_fdata().astype(int)
            zooms = img_ref.header.get_zooms()

            mod03.visualiser_segmentation(
                data_ref, data_seg, zooms,
                titre=f'Segmentation BraTS -- {PATIENT_ID}'
            )