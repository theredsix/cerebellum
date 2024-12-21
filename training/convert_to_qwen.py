#!/usr/bin/env python3

"""
Convert the data produced by `mind2web_to_molmo.py` into a single JSON dataset
in the "image_example_dataset" style (or similar), complete with images saved
as PNG files and a single JSON output referencing those images. This script
also illustrates how to incorporate the tool descriptions into a system prompt
for each example.

Example usage:
--------------
python convert_molmo_to_sharegpt.py \
    --input_dir molmo \
    --tool_desc tool_use_desc.json \
    --output_json tooluse_dataset.json \
    --image_dir images \
    --max_files 10 \
    --max_lines 50

Behavior:
---------
1. Reads tool descriptions from `tool_use_desc.json`.
2. Iterates over .jsonl files in `--input_dir` (output from `mind2web_to_molmo.py`).
3. For each .jsonl file, each line is a conversation example:
    - Extract the system prompt + user task from the first two messages
      in that example.
    - Insert the tool descriptions into the system prompt.
    - Extract the screenshot from the second-to-last assistant message
      (the "tool_result" block).
    - Convert the screenshot from base64 to a PNG image and store it
      in `--image_dir`.
    - Construct the final conversation in the format:
        {
          "messages": [
            {"role": "user", "content": "<system prompt + tool desc + user task>"},
            {"role": "assistant", "content": "<screenshot placeholder>"},
            {"role": "user", "content": "<image placeholder> <tooluse result>"},
            {"role": "assistant", "content": "<tool use>"}
          ],
          "images": ["images/123.png"]
        }
4. Append the example to a list and finally save them all into
   `--output_json` as a JSON array.
5. Supports optional flags `--max_files` and `--max_lines` to limit
   the amount of data processed.
"""

import argparse
import base64
import json
import os
import re
import sys


def load_tool_descriptions(desc_path: str) -> str:
    """
    Load the JSON array of tool descriptions from `tool_use_desc.json`
    and produce a summarized text version for usage in the system prompt.
    """
    with open(desc_path, "r", encoding="utf-8") as f:
        tools = json.load(f)

    return tools
    # # We'll create a text block that describes each function in a concise manner.
    # lines = []
    # for item in tools:
    #     fn = item.get("function", {})
    #     name = fn.get("name", "unknown_tool")
    #     desc = fn.get("description", "")
    #     lines.append(f"Tool name: {name}\nDescription: {desc}\n")
    # return "\n".join(lines)


def sanitize_filename(text: str) -> str:
    """
    Create a reasonable filename from a text snippet by removing
    or replacing characters that are not file-system friendly.
    """
    # Keep only alphanumeric characters, underscore, dash, or dot
    text = re.sub(r"[^A-Za-z0-9_\-\.]+", "_", text)
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Convert molmo output to a single JSON dataset with image references."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="molmo",
        help="Directory containing the .jsonl files from mind2web_to_molmo.py",
    )
    parser.add_argument(
        "--tool_desc",
        type=str,
        default="tool_use_desc.json",
        help="Path to the tool descriptions JSON file",
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default="tooluse_dataset.json",
        help="Path to the combined output JSON file",
    )
    parser.add_argument(
        "--image_dir",
        type=str,
        default="images",
        help="Folder to store extracted screenshot images",
    )
    parser.add_argument(
        "--max_files",
        type=int,
        default=0,
        help="Max number of files to process (0 for no limit)",
    )
    parser.add_argument(
        "--max_lines",
        type=int,
        default=0,
        help="Max number of lines per file (0 for no limit)",
    )
    args = parser.parse_args()

    # Create images folder if needed
    if not os.path.exists(args.image_dir):
        os.makedirs(args.image_dir)

    # Load tool descriptions as a text block
    tool_description_text = load_tool_descriptions(args.tool_desc)

    # We'll accumulate the final data here
    final_dataset = []

    all_files = [
        f
        for f in os.listdir(args.input_dir)
        if os.path.isfile(os.path.join(args.input_dir, f)) and f.endswith(".jsonl")
    ]
    all_files.sort()

    # Optionally limit the number of files
    if args.max_files > 0:
        all_files = all_files[: args.max_files]

    file_counter = 0
    global_image_counter = 0

    for filename in all_files:
        file_counter += 1
        file_path = os.path.join(args.input_dir, filename)
        print(f"Processing file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            line_counter = 0
            for line in f:
                line_counter += 1
                # Optionally limit lines
                if args.max_lines > 0 and (line_counter > args.max_lines):
                    break

                try:
                    conversation = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Warning: could not parse line {line_counter} in {filename}")
                    continue

                # conversation is an array of messages
                # We expect something like:
                # [
                #   {"role": "system", "content": "..."},
                #   {"role": "user", "content": "..."},
                #   {"role": "assistant", "content": [...]},
                #   {"role": "user", "content": [...]},
                #   ...
                # ]
                #
                # We want to assemble four messages in this final structure:
                #
                # messages = [
                #   { "role": "user", "content": "<system + tool desc + task>" },
                #   { "role": "assistant", "content": "<screenshot>" },
                #   { "role": "user", "content": "<image> <tooluse result>" },
                #   { "role": "assistant", "content": "<tool use>" }
                # ]
                #
                # Then images: [ "images/xxx.png" ]
                #
                # Let's define our strategy:
                # 1) The first message is user: we combine the system prompt, tool desc, and user task.
                #    - We'll guess the system prompt is conversation[0]["content"] (role=system).
                #    - The user task is likely conversation[1]["content"] (role=user).
                #
                # 2) The second message is the assistant showing the screenshot, which we typically get
                #    from the second-to-last message's "tool_result" content. But let's see how the logic
                #    is structured in the example from "molmo_example.jsonl".
                #
                #    Typically, the "tool_result" (the user's message with "content":[{"type":"tool_result", ...}])
                #    has the screenshot as base64. We need to decode it and save as PNG. Then we store a text
                #    placeholder: e.g. "Screenshot of the browser: screenshot_XXXX.png" or similar.
                #
                #    For simplicity, let's do <screenshot #N> or "Screenshot: <file path>".
                #
                # 3) The third message is user: "<image> <tooluse result>".
                #    The "tooluse result" is presumably the text from the user block that is not an image.
                #
                # 4) The final message is assistant: the last tool use, e.g. "Perform a left click on element".
                #
                # We'll assume each JSON line is a *complete conversation*, so we only extract the relevant
                # pieces from it. We'll do minimal logic here:
                #   - system_prompt = conversation[0]["content"]
                #   - user_task     = conversation[1]["content"]
                #   - screenshot base64 from the second to last user message that has "tool_result" with image?
                #   - the final assistant message is the last "assistant" role, e.g. conversation[-1]["content"] (the tool use).
                #
                # Implementation detail: The conversation from mind2web_to_molmo is an array of messages, some are user, some are assistant.
                #   The user messages that contain "tool_result" are the observations from a screenshot.
                #   The assistant messages that contain "tool_use" are the function calls.
                #
                # We'll do a simplistic approach to find them:
                #    last_assistant_index = the last item in conversation with role=assistant
                #    second_to_last_assistant_index = the second to last item in conversation with role=assistant
                #
                # Then parse out:
                #   screenshot base64 => from second_to_last_assistant_index's preceding user message?
                #   Actually, from the examples, the "tool_result" is user content. So we want the second to last occurrence of role="user" that has an image in the content.
                #
                # We'll do a quick scan from the end to find the user block that has "type": "tool_result" with "content": [..., {"type": "image", ...}].
                # Then the last assistant block is the final tool use.
                #

                # 1) Gather system prompt + user task
                if len(conversation) < 4:
                    # Not enough messages
                    continue

                # The first system message content
                if conversation[0]["role"] == "system":
                    # conversation[0]["content"] can be str or something else
                    # It's presumably a string.
                    system_msg = conversation[0]["content"]
                    if not isinstance(system_msg, str):
                        # Sometimes it's structured differently. We'll try converting to string
                        system_msg = json.dumps(system_msg)
                else:
                    raise ValueError("First entry should be system prompt")

                # The second message is presumably the user prompt with the <USER_TASK>
                user_task = ""
                if conversation[1]["role"] == "user":
                    # This might also be a string or array
                    # We want to ensure we unify it into text
                    user_task_content = conversation[1]["content"]
                    if isinstance(user_task_content, list):
                        user_task = json.dumps(user_task_content)
                    elif isinstance(user_task_content, str):
                        user_task = user_task_content
                else:
                    # If we don't have a user prompt as the second message, skip
                    raise ValueError("Second entry should be task")

                # Combine them + tool descriptions
                # For clarity, let's do something like:
                # <system prompt>\n\nTool Descriptions:\n<tool_description_text>\n\n<task>
                combined_user_msg = (
                    f"{system_msg}\n\n"
                    f"Tool Descriptions:\n{tool_description_text}\n"
                    f"{user_task}"
                )
                # Second to last message is the screen shhot
                if (conversation[-2]["role"] == "user") and conversation[-2]["content"][
                    0
                ]["type"] == "tool_result":
                    for c in conversation[-2]["content"][0]["content"]:
                        if c["type"] == "text":
                            mouse_state = json.dumps(c["value"])
                        elif c["type"] == "image":
                            screenshot_base64 = c["source"]["data"]
                else:
                    raise ValueError("Second to last entry should be screenshot")

                # Now build the final example
                # Decode the base64 string and save it as an image file
                image_data = base64.b64decode(screenshot_base64)
                jpg_filename = f"image_{global_image_counter}.jpg"
                image_path = os.path.join(args.image_dir, jpg_filename)
                with open(image_path, "wb") as img_file:
                    img_file.write(image_data)
                global_image_counter += 1

                example_obj = {
                    "messages": [
                        {
                            "role": "user",
                            "content": combined_user_msg,
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps(conversation[-3]["content"]),
                        },
                        {
                            "role": "user",
                            "content": f"<image> {mouse_state}",
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps(conversation[-1]["content"]),
                        },
                    ],
                    "images": (
                        [f"{args.image_dir}/{jpg_filename}"] if jpg_filename else []
                    ),
                }

                final_dataset.append(example_obj)

        print(f"Finished file: {filename}  (examples so far: {len(final_dataset)})")

    # Write out the final dataset
    with open(args.output_json, "w", encoding="utf-8") as outf:
        json.dump(final_dataset, outf, indent=2)

    print(
        f"\nAll done! Wrote {len(final_dataset)} total examples to {args.output_json}"
    )


if __name__ == "__main__":
    main()
