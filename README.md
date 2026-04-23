# Pipeline IRM Cérébrale — Segmentation Tumorale BraTS

Pipeline modulaire de segmentation automatique de tumeurs cérébrales (glioblastomes) à partir d'IRM multi-modales. Utilise le dataset UPENN-GBM de TCIA et le modèle nnU-Net pré-entraîné sur BraTS 2021.

## Contexte

Ce projet s'inscrit dans le cadre d'un stage de recherche (Rennes 2025) sur le projet EpiBrainRad, portant sur l'analyse dose-réponse des anomalies radio-induites de la substance blanche chez les patients atteints de glioblastome traités par radiothérapie. Le pipeline permet d'automatiser la segmentation des tumeurs cérébrales pour l'analyse statistique ultérieure.

## Architecture du pipeline

```
TCIA (UPENN-GBM)
      |
      v
01 - Téléchargement DICOM (4 modalités : T1, T1CE, T2, FLAIR)
      |
      v
02 - Conversion DICOM -> NIFTI (dcm2niix, nommage BraTS)
      |     _0000.nii.gz = T1CE (3D GAD, avec contraste gadolinium)
      |     _0001.nii.gz = T1   (sans contraste)
      |     _0002.nii.gz = T2
      |     _0003.nii.gz = FLAIR
      |
      v
03 - Visualisation (3 plans anatomiques, slider interactif)
      |
      v
04 - Co-registration (ANTs, recalage rigide sur T1CE)
      |     Le patient bouge entre chaque acquisition.
      |     On aligne T1, T2, FLAIR sur T1CE (référence).
      |
      v
05 - Inférence nnU-Net (segmentation tumorale BraTS)
            label 1 = NCR  (nécrose)
            label 2 = ED   (œdème péritumoral)
            label 4 = ET   (tumeur rehaussante)
```

## Structure du repository

```
projet_irm/
├── Main.py                       # Orchestrateur du pipeline complet
├── 01_download_dicom.py           # Téléchargement DICOM depuis TCIA
├── 02_convert_dicom_to_nifti.py   # Conversion DICOM -> NIFTI (dcm2niix)
├── 03_visualize_nifti.py          # Visualisation interactive des volumes
├── 04_coregistration.py           # Co-registration des 4 modalités (ANTs)
├── 05_nnunet_inference.py         # Inférence nnU-Net (segmentation BraTS)
├── requirements.txt               # Dépendances Python
├── README.md                      # Ce fichier
└── data/                          # (non inclus) généré automatiquement
```

## Prérequis

### Environnement

- Python 3.11+
- NVIDIA GPU avec CUDA (testé sur RTX 4060 Laptop, 8GB VRAM, CUDA 12.8)
- Windows, Linux ou macOS

### Outils externes

- **dcm2niix** : conversion DICOM → NIFTI
  - Télécharger depuis https://github.com/rordenlab/dcm2niix/releases
  - Placer l'exécutable à la racine du projet (ou adapter le chemin dans Main.py)

### Modèle pré-entraîné

Le pipeline utilise un modèle nnU-Net v2 pré-entraîné sur le dataset **BraTS 2021** par BAMF Health, disponible sur Zenodo (1.2 GB) :

https://zenodo.org/records/11582627

Télécharger `Dataset002_BRATS19.zip` et l'installer avec :

```bash
nnUNetv2_install_pretrained_model_from_zip chemin/vers/Dataset002_BRATS19.zip
```

## Installation

```bash
# Cloner le repository
git clone https://github.com/votre-username/projet_irm.git
cd projet_irm

# Créer un environnement virtuel
python -m venv env_seg
source env_seg/bin/activate  # Linux/Mac
# ou
env_seg\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

Configurer les variables d'environnement nnU-Net (à faire à chaque session) :

```powershell
# Windows PowerShell
$Env:nnUNet_raw = "C:\chemin\vers\nnUNet_raw"
$Env:nnUNet_preprocessed = "C:\chemin\vers\nnUNet_preprocessed"
$Env:nnUNet_results = "C:\chemin\vers\nnUNet_results"
```

```bash
# Linux/Mac
export nnUNet_raw="/chemin/vers/nnUNet_raw"
export nnUNet_preprocessed="/chemin/vers/nnUNet_preprocessed"
export nnUNet_results="/chemin/vers/nnUNet_results"
```

## Utilisation

### Exécution complète

Modifier le dictionnaire `EXECUTER` dans `Main.py` pour activer les étapes souhaitées :

```python
EXECUTER = {
    '01_download':     True,
    '02_convert':      True,
    '03_visualize':    True,
    '04_coregister':   True,
    '05_nnunet':       True,
}
```

Puis :

```bash
python Main.py
```

### Exécution étape par étape

Chaque script est autonome et peut être lancé indépendamment :

```bash
python 01_download_dicom.py
python 02_convert_dicom_to_nifti.py
python 03_visualize_nifti.py
python 04_coregistration.py
python 05_nnunet_inference.py
```

Les paramètres (patient_id, chemins) sont configurés dans le bloc `if __name__ == '__main__'` de chaque script.

## Convention de nommage BraTS

| Suffixe | Modalité | Description |
|---------|----------|-------------|
| _0000   | T1CE     | T1 avec contraste gadolinium (3D GAD) |
| _0001   | T1       | T1 sans contraste |
| _0002   | T2       | T2 |
| _0003   | FLAIR    | Fluid-Attenuated Inversion Recovery |

## Labels de segmentation BraTS

Attention : le dataset BraTS utilise la convention historique **0-1-2-4** (pas 0-1-2-3). Le label 3 est inexistant — anciennement "non-enhancing tumor", fusionné avec la nécrose dans le label 1.

| Label | Compartiment | Description |
|-------|-------------|-------------|
| 0     | Fond        | Tissu sain / arrière-plan |
| 1     | NCR         | Nécrose / tumeur non-rehaussante |
| 2     | ED          | Œdème péritumoral |
| 4     | ET          | Tumeur rehaussante |

## Fine-tuning sur données personnalisées

Le modèle pré-entraîné utilisé (BraTS 2021) peut être fine-tuné sur un dataset personnalisé pour améliorer les performances sur des données spécifiques (cohorte EpiBrainRad, segmentations Pixyl, autres centres hospitaliers).

### Cas d'usage

- Adapter le modèle à une distribution d'images différente (autre scanner, autre protocole)
- Intégrer des annotations manuelles d'experts (neuroradiologues)
- Améliorer la segmentation sur des sous-populations spécifiques (pédiatrie, gliomes de bas grade)

### Workflow prévu

```
Dataset personnalisé (NIFTI multi-modal + masques experts)
      |
      v
Conversion au format nnU-Net (imagesTr/, labelsTr/)
      |
      v
nnUNetv2_plan_and_preprocess -d DATASET_ID
      |
      v
Fine-tuning à partir des poids BraTS 2021
      |     nnUNetv2_train DATASET_ID 3d_fullres FOLD --pretrained_weights
      |
      v
Validation croisée 5-fold
      |
      v
Inférence avec le modèle fine-tuné
```

### Prérequis pour le fine-tuning

- 50+ patients avec segmentations expertes (recommandé 100+)
- Les 4 modalités par patient (T1, T1CE, T2, FLAIR)
- GPU avec ≥16 GB VRAM recommandé pour l'entraînement
- Durée estimée : 2-3 jours par fold sur RTX 4090

Documentation officielle du fine-tuning nnU-Net :
https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/pretraining_and_finetuning.md

## Librairies principales

- **tcia_utils** : API TCIA/NBIA pour télécharger les données DICOM
- **dcm2niix** : Conversion DICOM → NIFTI avec sidecars JSON BIDS
- **nibabel** : Lecture et manipulation de volumes NIFTI
- **antspyx** : Co-registration multi-modale (ANTs)
- **nnunetv2** : Inférence et fine-tuning du modèle de segmentation
- **torch** : Backend deep learning (nnU-Net)
- **matplotlib** : Visualisation interactive avec sliders

## Notes techniques

- Sur Windows, utiliser `python` (pas `py`) dans un virtualenv activé pour éviter les conflits de version.
- Les variables d'environnement PowerShell sont temporaires (perdues à la fermeture du terminal). Pour les rendre permanentes, les ajouter via Panneau de configuration > Variables d'environnement.
- Le recalage rigide ANTs (6 paramètres) suffit pour des IRM du même patient. Un recalage affine ou non-linéaire serait nécessaire pour du recalage inter-patients.
- nnU-Net attend un ordre précis des modalités. Vérifier que `_0000` correspond bien à T1CE pour le modèle BraTS 2021.
- Pour les modèles avec 5 folds, passer `-f 0 1 2 3 4` à `nnUNetv2_predict` pour utiliser l'ensemble complet.

## Licence

Ce projet a été développé à des fins académiques dans le cadre du stage EpiBrainRad (Rennes 2025).

## Contact

Pour toute question : vivian.artuose@example.com

## Références

- Isensee, F. et al. (2021). nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation. Nature Methods, 18(2), 203-211.
- Baid, U. et al. (2021). The RSNA-ASNR-MICCAI BraTS 2021 Benchmark on Brain Tumor Segmentation and Radiogenomic Classification. arXiv:2107.02314.
- Murugesan, G. K., Van Oss, J., McCrumb, D. (2024). Pretrained model for 3D semantic image segmentation of the brain tumor, necrosis, and edema from MRI scans. Zenodo.

---

**Note** : Les données TCIA (UPENN-GBM) ne sont pas incluses dans ce repository. Elles sont téléchargées automatiquement par le script `01_download_dicom.py` lors de l'exécution du pipeline.
