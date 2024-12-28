# Mind2Web Training Data Pipeline

This guide explains how to process the Mind2Web dataset into different training formats.

## Pipeline Overview

The pipeline consists of two main steps:
1. Download and preprocess raw Mind2Web data
2. Convert to your preferred format (either Molmo or LLaMA Factory)

## Step 1: Preprocess Mind2Web Data

```bash
python preprocess_mind2web.py \
--dataset_name osunlp/Multimodal-Mind2Web \
--subset train \
--output_dir mind2web
```

This downloads the Mind2Web dataset from HuggingFace and processes browser interactions into discrete steps, outputting JSONL files with normalized coordinates and screenshots.

## Step 2: Choose Your Format

### Option A: Convert to Molmo Format

```bash
python mind2web_to_molmo.py \
--input_dir mind2web \
--output_dir molmo
```

This converts the preprocessed data to Molmo's conversation format with system prompts and tool descriptions. You can then create a HuggingFace dataset:

```bash
python molmo_to_hfdataset.py \
--input_dir molmo \
--output_dir hf_dataset \
--dataset_name molmo_dataset
```

### Option B: Convert to LLaMA Factory Format

```bash
python mind2web_to_qwen_llama_factory.py \
--input_dir mind2web \
--output_json qwen_llamafactory.json \
--images_dir images \
--tool_json tool_use_desc.json
```

This converts the data to LLaMA Factory training format with image processing and proper JSON structure.

## Format Comparison

- **Molmo Format**: Optimized for conversation-style interactions with tools and system prompts
- **LLaMA Factory**: Enables training with the LLaMA Factory framework which has specific format requirements

Choose the format that best fits your training framework and approach.