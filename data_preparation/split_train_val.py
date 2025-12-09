import os
import shutil
import random

# Folders with your images and labels
source_folders = ['plate_labels', 'vehicle_images']  # Corrected

# Destination folders
dest_img_train = 'dataset/images/train'
dest_img_val = 'dataset/images/val'
dest_lbl_train = 'dataset/labels/train'
dest_lbl_val = 'dataset/labels/val'

# Create destination directories if they don't exist
for folder in [dest_img_train, dest_img_val, dest_lbl_train, dest_lbl_val]:
    os.makedirs(folder, exist_ok=True)

split_ratio = 0.8  # 80% train, 20% val

for folder in source_folders:
    images = [f for f in os.listdir(folder) if f.endswith(('.jpg', '.png'))]
    random.shuffle(images)
    
    split_index = int(len(images) * split_ratio)
    train_images = images[:split_index]
    val_images = images[split_index:]
    
    # Copy train images and labels
    for img in train_images:
        shutil.copy(os.path.join(folder, img), os.path.join(dest_img_train, img))
        lbl = img.rsplit('.', 1)[0] + '.txt'
        shutil.copy(os.path.join(folder, lbl), os.path.join(dest_lbl_train, lbl))
    
    # Copy val images and labels
    for img in val_images:
        shutil.copy(os.path.join(folder, img), os.path.join(dest_img_val, img))
        lbl = img.rsplit('.', 1)[0] + '.txt'
        shutil.copy(os.path.join(folder, lbl), os.path.join(dest_lbl_val, lbl))

print("Dataset split completed!")
