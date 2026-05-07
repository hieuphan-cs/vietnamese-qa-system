# Vietnamese QA system: pretrained fine-tuning & RAG pipeline in education domain

## Updating...


Scope: Rule in Education

Fine-tuned LLM + RAG

## Addition information:
- Authors: Hieu Phan, Tuan Nguyen, Nam Nguyen


# Chatbot Application with Gradio on Kaggle

This guide provides step-by-step instructions on how to deploy and run the fine-tuned chatbot application using Gradio on the Kaggle platform.

## Prerequisites
- A Kaggle account.
- The notebook file: `ui-chatbox-finetune.ipynb`.

## Deployment Steps

### 1. Upload the Notebook
- Log in to Kaggle and create a new notebook.
- Upload the file `ui-chatbox-finetune.ipynb` to the notebook editor.

### 2. Prepare the Dataset
- Access the link: https://www.kaggle.com/datasets/nguyentuan205/fine-tuned-dataset and dowload the dataset
- Navigate to the **Data** or **Input** section in the right sidebar.
- Click on **Add Data** and upload your `fine-tuned-model` folder.
- Name the dataset as `fine-tuned-dataset`. This ensures the notebook can correctly reference the model paths.

### 3. Path Configuration
Ensure that your notebook points to the correct directory. Update the `DATASET_ROOT` variable so that it matches the path of your dataset. Kaggle allows you to copy the dataset path directly.
### 4. Configure Settings
- Open the **Settings** panel of your notebook.
- Under **Accelerator**, select **GPU T4 x2**. This provides the necessary computational power for the model to run efficiently.

### 5. Launch the Application
- Click the **Run All** button at the top of the notebook.
- Wait for a few moments for the dependencies to install and the model to load.
- Scroll down to the output of the final cell. Look for the **Gradio public link** (e.g., `https://xxxx.gradio.live`).
- Click the link to open the chatbot interface in your browser.

### 6. Terminating the Session
- Once you are finished, remember to click **Stop Session** to conserve your GPU quota and stop any further billing or resource usage.

---
*Note: The Gradio public link is temporary and will expire once the session is stopped or after a certain period of inactivity.*
