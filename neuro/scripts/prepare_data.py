import argparse
import os


import numpy as np
import pandas as pd
from scipy.stats import truncnorm

volume_shape = np.array([256, 256, 256])
subvolume_shape = np.array([64, 64, 64])

half_subvolume_shape = subvolume_shape // 2

mus = np.array(
    [volume_shape[0] // 2, volume_shape[0] // 2, volume_shape[0] // 2]
)
sigmas = np.array(
    [volume_shape[0] // 4, volume_shape[0] // 4, volume_shape[0] // 4]
)

truncnorm_coordinates = truncnorm(
    (half_subvolume_shape - mus + 1) / sigmas,
    (volume_shape - half_subvolume_shape - mus) / sigmas,
    loc=mus,
    scale=sigmas,
)


def coords_generator():
    """
    Args:
    """
    xyz = np.round(truncnorm_coordinates.rvs(size=(1, 3))[0]).astype("int")
    xyz_start = xyz - half_subvolume_shape
    xyz_end = xyz + half_subvolume_shape
    xyz_coords = np.vstack((xyz_start, xyz_end)).T
    return xyz_coords


def find_sample(path):
    """
    Args:
        path (str): path to mri images
    """
    labels_data = {"images": [], "labels": []}
    t = 0
    for case in os.listdir(path):
        case_folder = os.path.join(path, case)
        for person in os.listdir(case_folder):
            person_folder = os.path.join(case_folder, person)
            for train in os.listdir(person_folder):
                if train == "t1weighted.nii":
                    labels_data["images"].append(
                        os.path.join(person_folder, "t1weighted.nii")
                    )
                if train == "labels.DKT31.manual+aseg.nii":
                    labels_data["labels"].append(
                        os.path.join(
                            person_folder, "labels.DKT31.manual+aseg.nii"
                        )
                    )
                    print(t)
                    t += 1

    return pd.DataFrame(labels_data)


def generation_coordinates(data, n_samples):
    """
    Args:
        datapath (dataframe): dataframe with columns "images","labels"
        n_samples (int): numbers of samples
    """
    out_data = {"images": [], "labels": [], "coords": [], "split": []}
    for i in range(len(data)):
        if i < len(data) * 0.8:
            for coords in [coords_generator() for k in range(n_samples)]:
                out_data["images"].append(data.iloc[i, 0])
                out_data["labels"].append(data.iloc[i, 1])
                out_data["coords"].append(coords.tolist())
                out_data["split"].append(0)
        else:
            coords = coords_generator()
            out_data["images"].append(data.iloc[i, 0])
            out_data["labels"].append(data.iloc[i, 1])
            out_data["coords"].append(coords.tolist())
            out_data["split"].append(1)
    return pd.DataFrame(out_data)


def main(datapath, n_samples):
    """
    Args:
        datapath (str): path to mri files
        n_samples (int): numbers of samples
    """
    dataframe = generation_coordinates(find_sample(datapath), n_samples)
    dataframe.to_csv("/home/Bekovmi/neuro/bin/data/dataset.csv", index=False)
    dataframe[dataframe["split"] == 0][["images", "labels", "coords"]].to_csv(
        "/home/Bekovmi/neuro/bin/data/dataset_train.csv", index=False
    )
    dataframe[dataframe["split"] == 1][["images", "labels", "coords"]].to_csv(
        "/home/Bekovmi/neuro/bin/data/dataset_valid.csv", index=False
    )
    dataframe.iloc[-1, :2].to_csv("/home/Bekovmi/neuro/bin/data/dataset_infer.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="folders to files")
    parser.add_argument("datapath", type=str, help="dir with image")
    parser.add_argument("n_samples", type=int, help="number of sample")
    params = parser.parse_args()

    main(params.datapath, params.n_samples)
