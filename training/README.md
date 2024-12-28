# Mind2Web Training Data Pipeline

This folder contains scripts to process the Mind2Web dataset into different training formats for various model training approaches.

## Pipeline Overview

1. Download and preprocess raw Mind2Web data
2. Convert to Molmo conversation format
3. Create HuggingFace dataset
4. Convert to LLaMA Factory format

## Usage

### 1. Preprocess Mind2Web Data

```bash
python preprocess_mind2web.py \
--dataset_name osunlp/Multimodal-Mind2Web \
--subset train \
--output_dir mind2web
```

Downloads Mind2Web dataset from HuggingFace and processes browser interactions into discrete steps, outputting JSONL files with normalized coordinates and screenshots.

### 2. Convert to Molmo Format

```bash
python mind2web_to_molmo.py \
--input_dir mind2web \
--output_dir molmo
```


Converts preprocessed data to Molmo's conversation format with system prompts and tool descriptions.

### 3. Create HuggingFace Dataset

```bash
python molmo_to_hfdataset.py \
--input_dir molmo \
--output_dir hf_dataset \
--dataset_name molmo_dataset
```


Processes Molmo JSONL files into a HuggingFace dataset format with proper image handling.

### 4. Convert to LLaMA Factory Format

```bash
python mind2web_to_qwen_llama_factory.py \
--input_dir mind2web \
--output_json qwen_llamafactory.json \
--images_dir images \
--tool_json tool_use_desc.json
```


Converts data to LLaMA Factory training format with image processing and proper JSON structure.

## Why Multiple Formats?

The pipeline creates multiple formats because:

1. **Molmo Format**: Optimized for conversation-style interactions with tools and system prompts
2. **HuggingFace Dataset**: Provides efficient data loading and processing during training
3. **LLaMA Factory**: Enables training with the LLaMA Factory framework which has specific format requirements

Each format serves different training frameworks and approaches, giving flexibility in how the data can be used for model training.

## Requirements

- Python 3.8+
- HuggingFace datasets
- Pillow
- tqdm

## Directory Structure

```
training/
├── preprocess_mind2web.py # Initial data processing
├── mind2web_to_molmo.py # Conversion to Molmo format
├── molmo_to_hfdataset.py # Creation of HF dataset
├── mind2web_to_qwen_llama_factory.py # Conversion to LLaMA Factory format
└── README.md # This file
```