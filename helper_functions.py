import numpy as np
import tensorflow as tf
from sklearn.metrics import roc_curve, auc, roc_auc_score, precision_recall_curve, average_precision_score
from sklearn.preprocessing import label_binarize
import matplotlib.pyplot as plt

def process_image(image_path, img_size=32):
    """
    Load and preprocess an image.
    
    Args:
    image_path (str): Path to the image.
    img_size (int): Size to which the image is to be resized.
    
    Returns:
    tf.Tensor: Processed image.
    """
    image = tf.io.read_file(image_path)
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.resize(image, [img_size, img_size])
    image = image / 255.0  # Normalize pixel values
    return image

def prepare_dataset_simple(dataframe, path_column, label_column, img_size=32, batch_size=32):
    """
    Prepare a dataset from a DataFrame.
    
    Args:
    dataframe (pd.DataFrame): DataFrame containing image paths and labels.
    path_column (str): Name of the column in DataFrame that contains image paths.
    label_column (str): Name of the column in DataFrame that contains labels.
    img_size (int): Size to which the images are to be resized.
    batch_size (int): Batch size used during dataset creation.
    
    Returns:
    tf.data.Dataset: Prepared dataset for model training.
    """
    image_paths = dataframe[path_column].values
    labels = dataframe[label_column].values

    dataset = tf.data.Dataset.from_tensor_slices((image_paths, labels))
    dataset = dataset.map(lambda x, y: (process_image(x, img_size), y), num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(batch_size)
    dataset = dataset.prefetch(buffer_size=tf.data.AUTOTUNE)
    return dataset

def display_random_images_with_predictions(test_dataset, y_true, y_pred_probs, total_images=9):
    """
    Display random test images along with predictions and true labels based on prior predictions and TensorFlow dataset.

    Args:
    test_dataset: TensorFlow dataset containing test images.
    y_true: True labels of the images.
    y_pred_probs: Predicted probabilities for each class by the model.
    total_images: Total number of images to display.
    """
    y_pred = np.argmax(y_pred_probs, axis=1)
    random_indices = np.random.choice(range(len(y_true)), size=total_images, replace=False)
    
    plt.figure(figsize=(12, 8))
    i = 1
    for index in random_indices:
        for img_index, (image, label) in enumerate(test_dataset.unbatch().as_numpy_iterator()):
            if img_index == index:
                plt.subplot(3, 3, i)
                plt.imshow(image)
                plt.title(f"True: {label}, Pred: {y_pred[index]}")
                plt.axis("off")
                i += 1
                break
    plt.tight_layout()
    plt.show()

def display_misclassified_images(test_dataset, y_true, y_pred, total_images=9):
    """
    Display a specified number of misclassified images based on prior predictions and TensorFlow dataset.

    Args:
    test_dataset: TensorFlow dataset containing test images.
    y_true: True labels of the images.
    y_pred: Predicted labels by the model.
    total_images: Total number of misclassified images to display.
    """
    misclassified_indices = np.where(y_pred != y_true)[0]
    selected_indices = np.random.choice(misclassified_indices, size=total_images, replace=False)
    
    plt.figure(figsize=(10, 10))
    i = 1
    for index in selected_indices:
        for img_index, (image, label) in enumerate(test_dataset.unbatch().as_numpy_iterator()):
            if img_index == index:
                plt.subplot(3, 3, i)
                plt.imshow(image)
                plt.title(f"True: {label}, Pred: {y_pred[index]}")
                plt.axis("off")
                i += 1
                break
    plt.tight_layout()
    plt.show()

def calculate_and_plot_roc_curve(y_true, y_pred_probs, n_classes):
    """
    Micro ROC calculation.
    """
    # Binarization of labels
    y_true_binarized = label_binarize(y_true, classes=range(n_classes))
    
    # Calculate micro-average ROC
    fpr_micro, tpr_micro, _ = roc_curve(y_true_binarized.ravel(), y_pred_probs.ravel())
    roc_auc_micro = auc(fpr_micro, tpr_micro)

    # Calculate macro-average ROC
    roc_auc_macro = roc_auc_score(y_true_binarized, y_pred_probs, average='macro')
    fpr_macro, tpr_macro, _ = roc_curve(y_true_binarized.ravel(), y_pred_probs.ravel(), pos_label=1)
    
    # Plot ROC curve for micro-average
    plt.figure(figsize=(8, 6))
    plt.plot(fpr_micro, tpr_micro, label='Micro-average ROC curve (area = {0:0.2f})'.format(roc_auc_micro))

    # Plot ROC curve for macro-average
    plt.plot(fpr_macro, tpr_macro, label='Macro-average ROC curve (area = {0:0.2f})'.format(roc_auc_macro), linestyle='--')

    # Reference line
    plt.plot([0, 1], [0, 1], 'k--')

    # Plot settings
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend(loc="lower right")
    plt.show()

def calculate_and_plot_precision_recall_curve(y_true, y_pred_probs, n_classes):
    """
    Calculate and draw precision-recall curve.
    """
    y_true_binarized = label_binarize(y_true, classes=range(n_classes))
    precision = dict()
    recall = dict()
    average_precision = dict()

    for i in range(n_classes):
        precision[i], recall[i], _ = precision_recall_curve(y_true_binarized[:, i], y_pred_probs[:, i])
        average_precision[i] = average_precision_score(y_true_binarized[:, i], y_pred_probs[:, i])

    precision["macro"], recall["macro"], _ = precision_recall_curve(y_true_binarized.ravel(), y_pred_probs.ravel())
    average_precision["macro"] = average_precision_score(y_true_binarized, y_pred_probs, average="macro")

    plt.figure(figsize=(8, 6))
    plt.plot(recall['macro'], precision['macro'], label='Macro-average Precision-Recall curve (average precision = {0:0.2f})'.format(average_precision['macro']))
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    plt.title('Macro-average Precision-Recall Curve')
    plt.legend(loc="lower left")
    plt.show()

def plot_training_history_class(history):
    """
    Visualize the accuracy and loss history during training and validation.

    Args:
    history: History object returned from the model's fit() method.
    """
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epochs_range = range(len(acc))

    plt.figure(figsize=(16, 8))
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy')
    plt.legend(loc='lower right')
    plt.title('Training and Validation Accuracy')

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss')
    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.legend(loc='upper right')
    plt.title('Training and Validation Loss')
    plt.show()
