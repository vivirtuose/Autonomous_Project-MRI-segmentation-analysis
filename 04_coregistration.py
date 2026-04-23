"""
04_coregistration.py
Co-registration des 4 modalites IRM sur un referentiel commun (T1CE)
via ANTs (antspyx). Le patient bouge entre les acquisitions de chaque
modalite, donc les voxels ne sont pas alignes spatialement.
Le recalage rigide aligne T1, T2 et FLAIR sur T1CE.
"""

import os
import shutil
import ants


def verifier_volumes(nifti_dir, patient_id):
    """
    Charge les 4 volumes NIFTI et affiche leurs dimensions
    et espacement avant co-registration.

    Args:
        nifti_dir (str): Dossier contenant les 4 fichiers NIFTI
        patient_id (str): Identifiant du patient

    Returns:
        dict: Dictionnaire {suffixe: objet ANTsImage}
    """
    suffixes = {
        '_0000': 'T1CE',
        '_0001': 'T1',
        '_0002': 'T2',
        '_0003': 'FLAIR',
    }

    volumes = {}
    print("=== Volumes avant co-registration ===")
    for suffixe, nom in suffixes.items():
        chemin = os.path.join(nifti_dir, f'{patient_id}{suffixe}.nii.gz')
        img = ants.image_read(chemin)
        volumes[suffixe] = img
        print(f"  {nom:6} : {img.shape}  -- espacement {img.spacing}")

    return volumes


def coregistrer_modalites(nifti_dir, output_dir, patient_id):
    """
    Recale T1, T2 et FLAIR sur T1CE par transformation rigide.

    La transformation rigide utilise 6 parametres :
      - 3 rotations (autour des axes X, Y, Z)
      - 3 translations (le long des axes X, Y, Z)
    Elle ne deforme pas le volume, elle le repositionne seulement.

    T1CE est choisi comme reference car il a generalement
    la meilleure resolution spatiale (acquisition 3D).

    Args:
        nifti_dir (str): Dossier contenant les 4 NIFTI d'entree
        output_dir (str): Dossier de sortie pour les volumes recales
        patient_id (str): Identifiant du patient
    """
    os.makedirs(output_dir, exist_ok=True)

    # Image fixe = T1CE (reference haute resolution)
    t1ce = ants.image_read(
        os.path.join(nifti_dir, f'{patient_id}_0000.nii.gz')
    )

    # Modalites a recaler sur T1CE
    modalites_mobiles = {
        '_0001': 'T1',
        '_0002': 'T2',
        '_0003': 'FLAIR',
    }

    for suffixe, nom in modalites_mobiles.items():
        print(f"  Co-registration {nom} -> T1CE...")

        mobile = ants.image_read(
            os.path.join(nifti_dir, f'{patient_id}{suffixe}.nii.gz')
        )

        # Recalage rigide
        # fixed  : image de reference (ne bouge pas)
        # moving : image a recaler (sera transformee)
        # type_of_transform : 'Rigid' = rotation + translation seulement
        registration = ants.registration(
            fixed=t1ce,
            moving=mobile,
            type_of_transform='Rigid'
        )

        # Sauvegarder l'image recalee
        # registration['warpedmovout'] = image mobile apres transformation
        output_path = os.path.join(
            output_dir, f'{patient_id}{suffixe}_coreg.nii.gz'
        )
        ants.image_write(registration['warpedmovout'], output_path)
        print(f"  {nom} recale -> {output_path}")

    # Copier T1CE tel quel (deja dans son propre espace)
    src = os.path.join(nifti_dir, f'{patient_id}_0000.nii.gz')
    dst = os.path.join(output_dir, f'{patient_id}_0000_coreg.nii.gz')
    shutil.copy(src, dst)
    print(f"  T1CE copie comme reference")


def verifier_coregistration(output_dir):
    """
    Verifie que tous les volumes co-registres ont les memes
    dimensions et le meme espacement.

    Args:
        output_dir (str): Dossier contenant les volumes recales
    """
    print("\n=== Verification apres co-registration ===")
    for f in sorted(os.listdir(output_dir)):
        if f.endswith('.nii.gz'):
            img = ants.image_read(os.path.join(output_dir, f))
            print(f"  {f} : {img.shape} -- {img.spacing}")


# ============================================================
# EXECUTION
# ============================================================

if __name__ == '__main__':

    PATIENT_ID = 'UPENN-GBM-00283'
    DATA_DIR   = './data'
    NIFTI_DIR  = os.path.join(DATA_DIR, f'{PATIENT_ID}_4mod_nifti')
    OUTPUT_DIR = os.path.join(DATA_DIR, f'{PATIENT_ID}_coreg')

    print(f"=== Co-registration pour {PATIENT_ID} ===\n")

    verifier_volumes(NIFTI_DIR, PATIENT_ID)
    print()
    coregistrer_modalites(NIFTI_DIR, OUTPUT_DIR, PATIENT_ID)
    verifier_coregistration(OUTPUT_DIR)

    print("\nTermine.")
