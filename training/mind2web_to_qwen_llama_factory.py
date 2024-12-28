"""

Example usage:
--------------
python mind2web_to_qwen_llama_factory.py --input_dir mind2web/ --output_json qwen_llamafactory.json --images_dir images --tool_json tool_use_desc.json
--------------
"""

import argparse
import base64
import io
import json
import math
import os
import copy

from PIL import Image

# Import classes and functions from the reference file
from preprocess_mind2web import Coordinate, generate_tool_id, ScrollBar

CURSOR_64 = "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAQCAYAAAAvf+5AAAAAw3pUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjabVBRDsMgCP33FDuC8ijF49i1S3aDHX9YcLFLX+ITeOSJpOPzfqVHBxVOvKwqVSQbuHKlZoFmRzu5ZD55rvX8Uk9Dz2Ql2A1PVaJ/1MvPwK9m0TIZ6TOE7SpUDn/9M4qH0CciC/YwqmEEcqGEQYsvSNV1/sJ25CvUTxqBjzGJU86rbW9f7B0QHSjIxoD6AOiHE1oXjAlqjQVyxmTMkJjEFnK3p4H0BSRiWUv/cuYLAAABhWlDQ1BJQ0MgcHJvZmlsZQAAeJx9kT1Iw0AYht+2SqVUHCwo0iFD1cWCqIijVqEIFUKt0KqDyaV/0KQhSXFxFFwLDv4sVh1cnHV1cBUEwR8QZwcnRRcp8buk0CLGg7t7eO97X+6+A/yNClPNrnFA1SwjnUwI2dyqEHxFCFEM0DoqMVOfE8UUPMfXPXx8v4vzLO+6P0evkjcZ4BOIZ5luWMQbxNObls55nzjCSpJCfE48ZtAFiR+5Lrv8xrnosJ9nRoxMep44QiwUO1juYFYyVOIp4piiapTvz7qscN7irFZqrHVP/sJwXltZ5jrNKJJYxBJECJBRQxkVWIjTrpFiIk3nCQ//kOMXySWTqwxGjgVUoUJy/OB/8Lu3ZmFywk0KJ4DuF9v+GAaCu0Czbtvfx7bdPAECz8CV1vZXG8DMJ+n1thY7Avq2gYvrtibvAZc7wOCTLhmSIwVo+gsF4P2MvikH9N8CoTW3b61znD4AGepV6gY4OARGipS97vHuns6+/VvT6t8Ph1lyr0hzlCAAAA14aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOjFiYzFkZjE3LWM5YmMtNGYzZi1hMmEzLTlmODkyNWNiZjY4OSIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo4YTUyMWJhMC00YmNlLTQzZWEtYjgyYS04ZGM2MTBjYmZlOTgiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplODQ3ZjUxNC00MWVlLTQ2ZjYtOTllNC1kNjI3MjMxMjhlZTIiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE3MzAxNTc3NjY5MTI3ODciCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zOCIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQ6MTA6MjhUMTY6MjI6NDYtMDc6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDI0OjEwOjI4VDE2OjIyOjQ2LTA3OjAwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZTVjOTM2ZDYtYjMzYi00NzM4LTlhNWUtYjM3YTA5MzdjZDAxIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyNC0xMC0yOFQxNjoyMjo0Ni0wNzowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz5/5aQ8AAAABmJLR0QAcgByAAAtJLTuAAAACXBIWXMAAABZAAAAWQGqnamGAAAAB3RJTUUH6AocFxYuv5vOJAAAAHhJREFUKM+NzzEOQXEMB+DPYDY5iEVMIpzDfRxC3mZyBK7gChZnELGohaR58f7a7dd8bVq4YaVQgTvWFVjCUcXxA28qcBBHFUcVRwWPPuFfXVsbt0PPnLBL+dKHL+wxxhSPhBcZznuDXYKH1uGzBJ+YtPAZRyy/jTd7qEoydWUQ7QAAAABJRU5ErkJggg=="
CURSOR_BYTES = base64.b64decode(CURSOR_64)
cursor_img = Image.open(io.BytesIO(CURSOR_BYTES))

system_prompt = """\
Use a mouse and keyboard to interact with a computer, and take screenshots.
* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.
* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try taking another screenshot.
* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.
* If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.
* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.

<SYSTEM_CAPABILITY>
* You are a computer use tool that is controlling a browser in fullscreen mode to complete a goal for the user. The goal is listed below in <USER_TASK>.
* The browser operates in fullscreen mode, meaning you cannot use standard browser UI elements like STOP, REFRESH, BACK, or the address bar. You must accomplish your task solely by interacting with the website's user interface or calling "stop_browsing"
* After each action, you will be provided with mouse position, and a screenshot.
* Use the Page_down or Page_up keys to scroll through the webpage. If the website is scrollable, a gray rectangle-shaped scrollbar will appear on the right edge of the screenshot. Ensure you have scrolled through the entire page before concluding that content is unavailable.
* The mouse cursor will appear as a black arrow in the screenshot. Use its position to confirm whether your mouse movement actions have been executed successfully. Ensure the cursor is correctly positioned over the intended UI element before executing a click command.
* Follow all directions from the <IMPORTANT> section below. 
* The current date is {datetime.now().isoformat()}.
</SYSTEM_CAPABILITY>

The user will ask you to perform a task and you should use their browser to do so. After each step, analyze the screenshot and carefully evaluate if you have achieved the right outcome. Explicitly show your thinking for EACH function call: "I have evaluated step X..." If not correct, try again. Only when you confirm a step was executed correctly should you move on to the next one. You should always call a tool! Always return a tool call. Remember call the stop_browsing tool when you have achieved the goal of the task. Use keyboard shortcuts to navigate whenever possible.

<IMPORTANT>
* After moving the mouse to the desired location, always perform a left-click to ensure the action is completed.
* You will use information provided in user's <USER DATA> to fill out forms on the way to your goal.
* Ensure that any UI element is completely visible on the screen before attempting to interact with it.
</IMPORTANT>
"""


def mark_screenshot(
    img_buffer: bytes,
    mouse_position: Coordinate,
    scrollbar: ScrollBar,
) -> str:
    """
    Adds scrollbar and cursor overlays to a screenshot, then returns a base64-encoded JPEG.

    Args:
        img_buffer (bytes): Raw bytes of the screenshot image.
        mouse_position (Coordinate): x,y position of the mouse cursor.
        scrollbar (ScrollBar): ScrollBar object with scrollbar dimensions and position.

    Returns:
        str: Base64-encoded string of the modified screenshot.
    """
    with Image.open(io.BytesIO(img_buffer)) as img:
        width, height = img.size

        # Create scrollbar overlay
        scrollbar_width = 10
        scrollbar_height = int(height * scrollbar.height)
        scrollbar_top = int(height * scrollbar.offset)

        # Create gray rectangle for the scrollbar with ~80% opacity
        scrollbar_img = Image.new(
            "RGBA",
            (scrollbar_width, scrollbar_height),
            (128, 128, 128, int(255 * 0.8)),
        )

        # Create a copy to paste overlays
        composite = img.copy()
        composite.paste(
            scrollbar_img,
            (width - scrollbar_width, scrollbar_top),
            scrollbar_img,
        )

        # Add cursor
        composite.paste(
            cursor_img,
            (max(0, mouse_position.x), max(0, mouse_position.y)),
            cursor_img,
        )

        # Resize logic to keep it from exceeding 640x400
        aspect_ratio = composite.width / composite.height

        if composite.width > 640 or composite.height > 400:
            if aspect_ratio > (640 / 400):
                new_width = 640
                new_height = int(640 / aspect_ratio)
            else:
                new_height = 400
                new_width = int(400 * aspect_ratio)
        else:
            new_width, new_height = composite.width, composite.height

        composite = composite.resize((new_width, new_height), Image.LANCZOS)

        # Convert to base64
        output_buffer = io.BytesIO()
        composite.save(output_buffer, "JPEG", quality=85)
        return base64.b64encode(output_buffer.getvalue()).decode("utf-8")


def load_tool_descriptions(desc_path: str) -> str:
    """
    Load the JSON array of tool descriptions from `tool_use_desc.json`
    and produce a summarized text version for usage in the system prompt.
    """
    with open(desc_path, "r", encoding="utf-8") as f:
        tools = json.dumps(json.load(f))

    return tools


def main() -> None:
    """
    Main function that reads .jsonl files from --input_dir and writes processed output to --output_dir.
    Each .jsonl file is processed to produce instructions for the browser-based steps.
    """
    parser = argparse.ArgumentParser(
        description="Convert JSONL logs into training data with screenshot overlays."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="mind2web",
        help="Directory containing input .jsonl files (default: mind2web).",
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default="mind2web_qwen",
        help="Output JSON for llama-factory dataset.",
    )
    parser.add_argument(
        "--images_dir",
        type=str,
        default="images",
        help="Directory for images to be stored",
    )
    parser.add_argument(
        "--tool_json",
        type=str,
        required=True,
        help="JSON file containing tool descriptions",
    )

    args = parser.parse_args()

    input_dir = args.input_dir
    output_json = args.output_json
    images_dir = args.images_dir

    # Load tool descriptions as a text block
    tool_description_text = load_tool_descriptions(args.tool_json)

    print(f"Reading from: {input_dir}")
    print(f"Writing to:   {output_json}")
    print(f"Saving images to: {images_dir}")

    final_dataset = []
    global_image_counter = 0

    # Iterate over each file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".jsonl"):
            file_path = os.path.join(input_dir, filename)
            print("Processing", filename)

            # Load all lines into list once
            with open(file_path, "r", encoding="utf-8") as file:
                lines_data = []
                for line in file:
                    json_object = json.loads(line)
                    lines_data.append(json_object)

            # The first line's "goal" -> This is the first message for every example
            goal = lines_data.pop(0)["goal"]

            # Message 1 - Goal
            initial_messages = [
                {
                    "role": "user",
                    "content": f"<USER_TASK>{goal}</USER_TASK>\n<USER_DATA>NONE</USER_DATA>",
                }
            ]

            # Message 2 - Assistant screenshot reason
            initial_messages.append(
                {
                    "role": "assistant",
                    "content": "Take a screenshot of the browser to understand the current webpage",
                }
            )

            # Message 3 - Screenshot tool use
            initial_messages.append(
                {
                    "role": "function_call",
                    "content": json.dumps({"name": "screenshot", "arguments": {}}),
                }
            )

            # Build incremental sequences
            for line in lines_data:

                # Copy Messages 1-3
                messages = copy.deepcopy(initial_messages)

                # Build initial screen shot response
                mouse = Coordinate(
                    x=math.floor(line["state"]["mouse"]["x"]),
                    y=math.floor(line["state"]["mouse"]["y"]),
                )

                normalized_mouse_x = int(
                    (mouse.x / float(line["state"]["width"])) * 1000
                )
                normalized_mouse_y = int(
                    (mouse.y / float(line["state"]["height"])) * 1000
                )

                # Message 4 - Screenshot result
                messages.append(
                    {
                        "role": "observation",
                        "content": f"<image>Mouse is at X: {normalized_mouse_x}, Y: {normalized_mouse_y}",
                    }
                )

                # Get information from example
                action_data = line["action"]

                # Message 5 - Next tool use reasoning
                messages.append(
                    {"role": "assistant", "content": f"{action_data['reasoning']}"}
                )

                # Build json for next tool use
                next_tool = {"name": action_data["action"], "arguments": {}}

                if action_data["text"] is not None:
                    next_tool["arguments"]["text"] = action_data["text"]
                if action_data["coordinate"] is not None:
                    x_coord, y_coord = action_data["coordinate"]
                    norm_x = int(
                        (float(x_coord) / float(line["state"]["width"])) * 1000
                    )
                    norm_y = int(
                        (float(y_coord) / float(line["state"]["height"])) * 1000
                    )
                    next_tool["arguments"]["coordinate"] = [
                        norm_x,
                        norm_y,
                    ]

                # Message 6 - Next tool use
                messages.append(
                    {
                        "role": "function_call",
                        "content": json.dumps(next_tool),
                    }
                )

                # Create the marked image
                decoded_img = base64.b64decode(line["state"]["screenshot"])
                marked_image = mark_screenshot(
                    decoded_img,
                    mouse,
                    ScrollBar(
                        offset=line["state"]["scrollbar"]["offset"],
                        height=line["state"]["scrollbar"]["height"],
                    ),
                )
                jpg_filename = f"image_{global_image_counter}.jpg"
                image_path = os.path.join(args.images_dir, jpg_filename)
                with open(image_path, "wb") as img_file:
                    img_file.write(base64.b64decode(marked_image))
                global_image_counter += 1

                # Construct complete example
                this_example = {
                    "messages": messages,
                    "system": f"{system_prompt}",
                    "tools": tool_description_text,
                    "images": (
                        [f"{args.images_dir}/{jpg_filename}"] if jpg_filename else []
                    ),
                }

                final_dataset.append(this_example)

        # Write out the final dataset
    with open(args.output_json, "w", encoding="utf-8") as outf:
        json.dump(final_dataset, outf, indent=2)

    print(
        f"\nAll done! Wrote {len(final_dataset)} total examples to {args.output_json}"
    )


if __name__ == "__main__":
    main()
