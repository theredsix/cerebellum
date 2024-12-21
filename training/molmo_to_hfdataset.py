"""
Convert base64-encoded Mind2Web-like data into a HuggingFace Dataset with images.

Example Usage:
--------------
python molmo_data_processor.py \
    --input_dir /path/to/mind2web \
    --output_dir /path/to/output \
    --dataset_name 'my-dataset-name' \
    --max_files 10 \
    --max_lines 50 \
    --test_mode

This script:
- Recursively reads .jsonl files from the specified --input_dir
- Converts any base64-encoded images into PIL images
- Processes each record into a structure suitable for a HuggingFace Dataset
- Saves the resulting dataset to the specified --output_dir
"""

import argparse
import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from datasets import Dataset, Features
from datasets import Image as DSImage
from datasets import Sequence, Value
from PIL import Image
from tqdm import tqdm


def convert_base64_to_image(base64_string: str) -> Image.Image:
    """
    Converts a base64 string to a PIL Image.

    Args:
        base64_string (str): Base64-encoded image data.

    Returns:
        Image.Image: Decoded PIL image.
    """
    # Remove prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    image_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_data))


def yield_jsonl_records(
    input_dir: Path, max_files: Optional[int] = None, max_lines: Optional[int] = None
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Generator function that yields records (lists of messages) from JSONL files.

    Args:
        input_dir (Path): Directory containing JSONL files.
        max_files (Optional[int]): Maximum number of files to process.
        max_lines (Optional[int]): Maximum number of lines to process per file.

    Yields:
        List[Dict[str, Any]]: The parsed JSON record from a single line of a JSONL file.
    """
    jsonl_files = list(input_dir.glob("*.jsonl"))

    if max_files is not None:
        jsonl_files = jsonl_files[:max_files]

    print(f"Processing {len(jsonl_files)} files...")

    for file_path in tqdm(jsonl_files, desc="Processing files"):
        line_count = 0

        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                if max_lines is not None and line_count >= max_lines:
                    break

                try:
                    record = json.loads(line)
                    yield record
                    line_count += 1
                except json.JSONDecodeError as e:
                    print(f"Error in {file_path}: {e}")
                    continue


def process_record(record: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a single JSONL record.

    Args:
        record (List[Dict[str, Any]]): List of messages from the JSONL record.

    Returns:
        Dict[str, Any]: Dictionary containing processed messages and images.
    """
    empty_content = {"text": None}
    messages = []
    images = []

    for msg in record:
        # Ensure msg["content"] is a list
        initial_content = (
            msg["content"]
            if isinstance(msg["content"], list)
            else [{"type": "text", "text": msg["content"]}]
        )

        # Append empty K-V pairs
        empty_filled_content = [
            {**empty_content, **content_entry} for content_entry in initial_content
        ]

        # Convert base64 images inside "tool_result" content
        for entry in empty_filled_content:
            if entry["type"] == "tool_result":
                for sub_entry in entry["content"]:
                    if sub_entry["type"] == "image":
                        pil_img = convert_base64_to_image(sub_entry["source"]["data"])
                        images.append(pil_img)
                        # Remove large base64 data from record, store an index
                        sub_entry["source"].pop("data")
                        sub_entry["source"]["image_index"] = len(images) - 1

        messages.append({**msg, "content": empty_filled_content})

    return {"messages": messages, "images": images}


def create_dataset_features() -> Features:
    """
    Create the feature schema for the dataset.

    Returns:
        Features: HuggingFace Features object defining column structure.
    """
    return Features(
        {
            "messages": Sequence(
                {
                    "role": Value("string"),
                    "content": Sequence(
                        {
                            "index": Value("null"),
                            "text": Value("string"),
                            "type": Value("string"),
                            "image_index": Value("int64"),
                        }
                    ),
                    "tool_calls": Sequence(
                        {
                            "name": Value("string"),
                            "arguments": Value("string"),
                        },
                        length=-1,
                    ),
                }
            ),
            "images": Sequence(DSImage()),
        }
    )


def process_and_save_dataset(
    input_dir: Path,
    output_dir: Path,
    max_files: Optional[int] = None,
    max_lines: Optional[int] = None,
    test_mode: bool = False,
) -> Dataset:
    """
    Process and save the dataset to disk. Reads JSONL files from input_dir,
    decodes images, and stores them in a HuggingFace Dataset.

    Args:
        input_dir (Path): Directory containing JSONL files.
        output_dir (Path): Directory to save the resulting dataset.
        max_files (Optional[int]): Max number of files to process (default: None).
        max_lines (Optional[int]): Max number of lines per file to process (default: None).
        test_mode (bool): Whether to save the dataset in a 'test' subdirectory.

    Returns:
        Dataset: The processed HuggingFace Dataset object.
    """
    print("Starting data processing...")

    # Create a Dataset from the generator
    dataset = Dataset.from_generator(
        lambda: (
            process_record(r)
            for r in yield_jsonl_records(input_dir, max_files, max_lines)
        )
    ).cast_column("images", Sequence(DSImage()))

    print(f"\nProcessed {len(dataset)} examples.")

    # Adjust output directory based on test_mode
    final_save_dir = output_dir / "test" if test_mode else output_dir
    final_save_dir.mkdir(parents=True, exist_ok=True)

    dataset.save_to_disk(str(final_save_dir))
    print(f"\nDataset saved to {final_save_dir}")

    # Verify the saved dataset
    print("\nVerifying saved dataset...")
    loaded_dataset = Dataset.load_from_disk(str(final_save_dir))
    print("Dataset size:", len(loaded_dataset))

    if len(loaded_dataset) > 0:
        print("\nFirst example:")
        first_example = loaded_dataset[0]
        print("Number of messages:", len(first_example["messages"]))
        print("Number of images:", len(first_example["images"]))

    return loaded_dataset


def main() -> None:
    """
    Main entrypoint. Parses command-line args and processes the dataset accordingly.
    """
    parser = argparse.ArgumentParser(
        description="Process base64-encoded web data into a HuggingFace Dataset."
    )

    parser.add_argument(
        "--input_dir",
        type=str,
        default="mind2web",
        help="Directory containing input JSONL files (default: mind2web).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="hf_dataset",
        help="Directory to store the output dataset (default: hf_dataset).",
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="molmo_dataset",
        help="Dataset name (not used directly, for reference/logging).",
    )
    parser.add_argument(
        "--max_files",
        type=int,
        default=None,
        help="Max number of files to process (default: None).",
    )
    parser.add_argument(
        "--max_lines",
        type=int,
        default=None,
        help="Max number of lines per file to process (default: None).",
    )
    parser.add_argument(
        "--test_mode",
        action="store_true",
        help="If set, saves the dataset in a subdirectory called 'test'.",
    )

    args = parser.parse_args()
    print(f"Running dataset processor for: {args.dataset_name}")

    process_and_save_dataset(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        max_files=args.max_files,
        max_lines=args.max_lines,
        test_mode=args.test_mode,
    )


if __name__ == "__main__":
    main()
