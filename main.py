import os

from tqdm import tqdm


def mean_files_in_folders(base_path):
    folder_file_counts = []

    # Iterate through all items in the base directory
    for item in tqdm(os.listdir(base_path)):
        item_path = os.path.join(base_path, item)

        # Check if it's a directory
        if os.path.isdir(item_path):
            # Count only files (not subdirectories)
            file_count = sum(
                1
                for f in os.listdir(item_path)
                if os.path.isfile(os.path.join(item_path, f))
            )
            folder_file_counts.append(file_count)

    if not folder_file_counts:
        return 0

    # Calculate mean
    mean_value = sum(folder_file_counts) / len(folder_file_counts)
    return mean_value


if __name__ == "__main__":
    base_path = "data/downloads/boe/"
    mean = mean_files_in_folders(base_path)
    print(f"Mean number of files per folder: {mean:.2f}")
