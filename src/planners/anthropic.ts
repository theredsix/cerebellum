import Anthropic from '@anthropic-ai/sdk';
import { ActionPlanner, BrowserAction, BrowserState, BrowserStep, Coordinate, ScrollBar } from '../browser';
import sharp from 'sharp';
import { BetaMessageParam } from '@anthropic-ai/sdk/resources/beta/messages/messages';

import fs from 'fs';
interface ScalingRatio {
    ratio: Coordinate;
    oldSize: Coordinate;
    newSize: Coordinate;
}

interface MsgOptions {
    mousePosition: boolean;
    screenshot: boolean;
    url: boolean;
}

const cursor64 = 'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAQCAYAAAAvf+5AAAAAw3pUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjabVBRDsMgCP33FDuC8ijF49i1S3aDHX9YcLFLX+ITeOSJpOPzfqVHBxVOvKwqVSQbuHKlZoFmRzu5ZD55rvX8Uk9Dz2Ql2A1PVaJ/1MvPwK9m0TIZ6TOE7SpUDn/9M4qH0CciC/YwqmEEcqGEQYsvSNV1/sJ25CvUTxqBjzGJU86rbW9f7B0QHSjIxoD6AOiHE1oXjAlqjQVyxmTMkJjEFnK3p4H0BSRiWUv/cuYLAAABhWlDQ1BJQ0MgcHJvZmlsZQAAeJx9kT1Iw0AYht+2SqVUHCwo0iFD1cWCqIijVqEIFUKt0KqDyaV/0KQhSXFxFFwLDv4sVh1cnHV1cBUEwR8QZwcnRRcp8buk0CLGg7t7eO97X+6+A/yNClPNrnFA1SwjnUwI2dyqEHxFCFEM0DoqMVOfE8UUPMfXPXx8v4vzLO+6P0evkjcZ4BOIZ5luWMQbxNObls55nzjCSpJCfE48ZtAFiR+5Lrv8xrnosJ9nRoxMep44QiwUO1juYFYyVOIp4piiapTvz7qscN7irFZqrHVP/sJwXltZ5jrNKJJYxBJECJBRQxkVWIjTrpFiIk3nCQ//kOMXySWTqwxGjgVUoUJy/OB/8Lu3ZmFywk0KJ4DuF9v+GAaCu0Czbtvfx7bdPAECz8CV1vZXG8DMJ+n1thY7Avq2gYvrtibvAZc7wOCTLhmSIwVo+gsF4P2MvikH9N8CoTW3b61znD4AGepV6gY4OARGipS97vHuns6+/VvT6t8Ph1lyr0hzlCAAAA14aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOjFiYzFkZjE3LWM5YmMtNGYzZi1hMmEzLTlmODkyNWNiZjY4OSIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo4YTUyMWJhMC00YmNlLTQzZWEtYjgyYS04ZGM2MTBjYmZlOTgiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplODQ3ZjUxNC00MWVlLTQ2ZjYtOTllNC1kNjI3MjMxMjhlZTIiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE3MzAxNTc3NjY5MTI3ODciCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zOCIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQ6MTA6MjhUMTY6MjI6NDYtMDc6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDI0OjEwOjI4VDE2OjIyOjQ2LTA3OjAwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZTVjOTM2ZDYtYjMzYi00NzM4LTlhNWUtYjM3YTA5MzdjZDAxIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyNC0xMC0yOFQxNjoyMjo0Ni0wNzowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz5/5aQ8AAAABmJLR0QAcgByAAAtJLTuAAAACXBIWXMAAABZAAAAWQGqnamGAAAAB3RJTUUH6AocFxYuv5vOJAAAAHhJREFUKM+NzzEOQXEMB+DPYDY5iEVMIpzDfRxC3mZyBK7gChZnELGohaR58f7a7dd8bVq4YaVQgTvWFVjCUcXxA28qcBBHFUcVRwWPPuFfXVsbt0PPnLBL+dKHL+wxxhSPhBcZznuDXYKH1uGzBJ+YtPAZRyy/jTd7qEoydWUQ7QAAAABJRU5ErkJggg==';
const cursorBuffer = Buffer.from(cursor64, 'base64');

export class AnthropicPlanner extends ActionPlanner {
    private client: Anthropic;
    private screenshotHistory: number;

    constructor(_none: undefined);
    constructor(apiKey: string);
    constructor(client: Anthropic);

    constructor(apiKeyOrClient: undefined | string | Anthropic, screenshotHistory: number = 1) {
        super();
        if (typeof apiKeyOrClient === 'string') {
            this.client = new Anthropic({ apiKey: apiKeyOrClient });
        } else if (typeof apiKeyOrClient === 'undefined') {
            this.client = new Anthropic();
        } else {
            this.client = apiKeyOrClient;
        }

        this.screenshotHistory = screenshotHistory;
    }

    public formatSystemPrompt(goal: string, additionalContext: string, additionalInstructions: string[]): string {
        const prompt = `<SYSTEM_CAPABILITY>
* You are using a browser in fullscreen mode to complete a goal for the user. The goal is listed below in <USER_GOAL>
* Information about the user THAT IS ALWAYS TRUE is included in <USER_DATA>. This information may or may not be relevant in completing your goal.
* The current mouse position is marked on the screenshot with a crosshair and also provided in the text: "After action mouse cursor is at X: <NUMBER> Y: <NUMBER>".
* You are provided with the browser's current URL in each step.
* You do not have the ability to scroll with a mouse wheel, use the Page_down or Page_up key to scroll.
* ALWAYS call a function
* DO NOT USE right or middle mouse buttons
* The current date is ${new Date().toString()}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* You will use information provided in <USER DATA> to fill out forms on the way to your goal.
* When completing forms, always scroll down until you can see the CONTINUE, NEXT or SUBMIT button.
* Always scroll a UI element fully into view before interacting with it.
* DO NOT MOVE THE MOUSE TO COORDINATES EQUAL TO WHERE IT CURRENTLY IS.
* Replan your move after each 'click', 'type' or 'key' action
* Always move the mouse to the center of a UI element when hovering or clicking. The center is defined as half of the height and half of the width of the UI element.
* Always output a chain of thought before calling a function. In your chain of thought, output the current state of the webpage and what you have are attempting to accomplish.
${additionalInstructions.map(instruction => `* ${instruction}`).join('\n')}
</IMPORTANT>"""

<USER_GOAL>
${goal}
</USER_GOAL>

<USER_DATA>
${additionalContext}
</USER_DATA>
`;

        return prompt;

    }

    private createToolUseId(): string {
        const prefix = 'toolu_';
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        const idLength = 24;
        let result = prefix;

        for (let i = 0; i < idLength; i++) {
            result += characters.charAt(Math.floor(Math.random() * characters.length));
        }

        return result;
    }

    public async getDimensions(screenshot: string): Promise<Coordinate> {
        const imgBuffer =  Buffer.from(screenshot, 'base64');
        const sharpImage = sharp(imgBuffer);
        const originalMeta = await sharpImage.metadata();

        return {
            x: originalMeta.width!,
            y: originalMeta.height!
        }
    }

    public async markScreenshot(imgBuffer: Buffer, mousePosition: Coordinate, scrollbar: ScrollBar): Promise<Buffer> {
        const sharpImage = sharp(imgBuffer);

        // Add scrollbar overlay
        const originalMeta = await sharpImage.metadata();
        const width = originalMeta.width!;
        const height = originalMeta.height!;
        
        // Create scrollbar overlay
        const scrollbarWidth = 10;
        const scrollbarHeight = Math.floor(height * scrollbar.height);
        const scrollbarTop = Math.floor(height * scrollbar.offset);

        console.log({
            scrollbarHeight,
            scrollbarWidth,
            scrollbarTop
        })
        
        // Create a gray rectangle for the scrollbar
        const scrollbarBuffer = await sharp({
            create: {
                width: scrollbarWidth,
                height: scrollbarHeight,
                channels: 4,
                background: { r: 128, g: 128, b: 128, alpha: 0.5 }
            }
        }).png().toBuffer();

        // Overlay the cursor on the screenshot, top left corner is the mouse location
        // Composite the scrollbar on the right side of the image
        const markedImage = await sharpImage.composite([{
            input: scrollbarBuffer,
            top: scrollbarTop,
            left: width - scrollbarWidth
        },
        {
            input: cursorBuffer,
            top: Math.max(0, mousePosition.y),
            left: Math.max(0, mousePosition.x)
        }]);

        // Convert the image back to base64
        const outputBuffer = await markedImage.toBuffer();
        return outputBuffer;
    }

    public async resizeScreenshot(screenshotBuffer: Buffer): Promise<Buffer> {
        const sharpImage = sharp(screenshotBuffer);
        const resizedImg = await sharpImage.resize(1280, 800, { fit: 'inside' });
        const imgBuffer = await resizedImg.toBuffer();

        return imgBuffer;
    }

    public async resizeImageToDimensions(screenshotBuffer: Buffer, newDim: Coordinate): Promise<Buffer> {
        const sharpImage = sharp(screenshotBuffer);
        const resizedImg = await sharpImage.resize(newDim.x, newDim.y, { fit: 'fill' });
        const imgBuffer = await resizedImg.toBuffer();

        return imgBuffer;
    }

    public getScalingRatio(origSize: Coordinate): ScalingRatio {
        const aspectRatio = origSize.x / origSize.y;

        let newWidth: number;
        let newHeight: number;

        if (aspectRatio > 1280 / 800) {
            newWidth = 1280;
            newHeight = Math.round(1280 / aspectRatio);
        } else {
            newHeight = 800;
            newWidth = Math.round(800 * aspectRatio);
        }

        const widthRatio = origSize.x / newWidth;
        const heightRatio = origSize.y / newHeight;

        return {
            ratio: { x: widthRatio, y: heightRatio },
            oldSize: { x: origSize.x, y: origSize.y },
            newSize: { x: newWidth, y: newHeight }
        };
    }

    private browserToLLMCoordinates(inputCoords: Coordinate, scaling: ScalingRatio): Coordinate {
        return {
            x: Math.min(Math.max(Math.round(inputCoords.x / scaling.ratio.x), 1), scaling.newSize.x),
            y: Math.min(Math.max(Math.round(inputCoords.y / scaling.ratio.y), 1), scaling.newSize.y),
        };
    }

    private llmToBrowserCoordinates(inputCoords: Coordinate, scaling: ScalingRatio): Coordinate {
        return {
            x: Math.min(Math.max(Math.round(inputCoords.x * scaling.ratio.x), 1), scaling.oldSize.x),
            y: Math.min(Math.max(Math.round(inputCoords.y * scaling.ratio.y), 1), scaling.oldSize.y),
        };
    }

    public async formatStateIntoMsg(toolCallId: string, currentState: BrowserState, options: MsgOptions): Promise<BetaMessageParam> {
        let resultText: string = '';
        const contentSubMsg: (Anthropic.Beta.Messages.BetaTextBlockParam | Anthropic.Beta.Messages.BetaImageBlockParam)[] = [];

        if (options.mousePosition) {
            const imgDim = {x: currentState.width, y: currentState.height};
            const scaling = this.getScalingRatio(imgDim);
            const scaledCoord = this.browserToLLMCoordinates(currentState.mouse, scaling);
            console.log(scaling);
            resultText += `After action mouse cursor is at X: ${scaledCoord.x}, Y: ${scaledCoord.y}\n\n`;
        }

        if (options.url) {
            resultText += `After action, the tab's URL is ${currentState.url}\n\n`;
        }

        if (options.screenshot) {
            resultText += 'Here is a screenshot of the browswer after the action was performed.\n\n';
            const imgBuffer = Buffer.from(currentState.screenshot, 'base64');
            const viewportImage = await this.resizeImageToDimensions(imgBuffer, {x: currentState.width, y: currentState.height});
            const markedImage = await this.markScreenshot(viewportImage, currentState.mouse, currentState.scrollbar);
            const resized = await this.resizeScreenshot(markedImage);
           
            fs.writeFileSync('tmp.png', resized, 'base64');
                        
            contentSubMsg.push({
                type: 'image',
                source: {
                    type: 'base64',
                    media_type: 'image/png',
                    data: resized.toString('base64')
                }
            });
        }

        if (resultText === '') { // Put a generic text explaination for no URL or result
            resultText += 'Action was performed.';
        }

        contentSubMsg.unshift({
            type: 'text',
            text: resultText.trim()
        });

        const resultMsg: BetaMessageParam = {
            role: 'user',
            content: [
                {
                    type: 'tool_result',
                    tool_use_id: toolCallId,
                    content: contentSubMsg
                }
            ]
        }

        return resultMsg;
    }

    public async formatIntoMessages(goal: string, currentState: BrowserState, sessionHistory: BrowserStep[]): Promise<BetaMessageParam[]> {
        const messages: BetaMessageParam[] = [];

        let toolId = this.createToolUseId();
        const msg0: BetaMessageParam = { role: 'user', content: [{ type: 'text', text: goal }] };
        const msg1: BetaMessageParam = {
            role: 'assistant', content: [
                {
                    type: 'tool_use',
                    id: toolId,
                    name: 'computer',
                    input: {
                        action: 'screenshot',
                        reasoning: 'Grab a view of the browser to understand what we are looking at.'
                    }
                }
            ]
        };

        messages.push(msg0);
        messages.push(msg1);

        for (let pastStepIdx = 0; pastStepIdx < sessionHistory.length; pastStepIdx++) {
            const pastStep = sessionHistory[pastStepIdx];

            const options: MsgOptions = {
                mousePosition: false,
                screenshot: false,
                url: true,
            }

            if (pastStepIdx <= (sessionHistory.length - this.screenshotHistory)) {
                options.url = true;
            }

            const resultMsg: BetaMessageParam = await this.formatStateIntoMsg(toolId, pastStep.state, options)

            messages.push(resultMsg);
            // Update the tool use id as now we're going to pretend to get the response
            toolId = this.createToolUseId();

            const actionMsg: BetaMessageParam = {
                role: 'assistant',
                content: [
                    {
                        type: 'tool_use',
                        id: toolId,
                        name: 'computer',
                        input: pastStep.action
                    }
                ]
            }

            messages.push(actionMsg);
        }

        const currentStateMessage: BetaMessageParam = await this.formatStateIntoMsg(toolId, currentState, { mousePosition: true, screenshot: true, url: true });
        messages.push(currentStateMessage);

        return messages;
    }

    public parseAction(message: Anthropic.Beta.Messages.BetaMessage, scaling: ScalingRatio, currentState: BrowserState): BrowserAction {
        // Collect all the text output as reasoning.
        const reasoning = message.content
            .filter((content) => content.type === 'text')
            .map((content) => content.text)
            .join(' ');

        const lastMessage = message.content[message.content.length - 1];
        if (typeof lastMessage === 'string') {
            return {
                action: 'failure',
                reasoning,
            };
        }

        if (lastMessage.type !== 'tool_use') {
            return {
                action: 'failure',
                reasoning,
            };
        }
        if (lastMessage.name === 'stop_browsing') {
            const input = lastMessage.input as {
                success: boolean;
                error?: string;
            };
            if (!input.success) {
                return {
                    action: 'failure',
                    reasoning,
                    text: input.error ?? 'Unknown error'
                };
            }
            return {
                action: 'success',
                reasoning,
                text: input.error ?? 'Unknown error'
            };
        }
        if (lastMessage.name !== 'computer') {
            return {
                action: 'failure',
                reasoning,
                text: 'Wrong message called'
            };
        }

        const { action, coordinate, text } = lastMessage.input as {
            action: string;
            coordinate?: [number, number];
            text?: string;
        };

        switch (action) {
            case 'key':
                // Treat scrolling actions in a special manner
                if (['page_down', 'pagedown'].includes(text?.trim() ?? '')) {
                    return {
                        action: 'scroll_down',
                        reasoning
                    }
                } else if (['page_up', 'pageup'].includes(text?.trim() ?? '')) {
                    return {
                        action: 'scroll_up',
                        reasoning
                    }
                }
                // Explicit fallthrough
            case 'type':
                if (!text) {
                    return {
                        action: 'failure',
                        reasoning,
                        text: `No text provided for ${action}`,
                    };
                } else {
                    return {
                        action,
                        reasoning,
                        text
                    }
                }
            case 'mouse_move':
            case 'left_click_drag':
                if (!coordinate) {
                    return { action: 'failure', reasoning, text: 'No coordinate provided' };
                } else {
                    // Scale back coordinates
                    const browserCoordinates = this.llmToBrowserCoordinates({x: coordinate[0], y: coordinate[1]}, scaling);

                    // Check if the browser coordinates match the current mouse position
                    if (browserCoordinates.x === currentState.mouse.x && browserCoordinates.y === currentState.mouse.y) {
                        // If coordinates match, dispatch a click event instead of moving the mouse
                        return { action: 'left_click', reasoning };
                    }
                    return { action, reasoning, coordinate: [browserCoordinates.x, browserCoordinates.y]};
                }
            case 'left_click':
            case 'right_click':
            case 'middle_click':
            case 'double_click':
            case 'screenshot':
            case 'cursor_position':
                return { action, reasoning };
            default:
                return {
                    action: 'failure',
                    reasoning,
                    text: `Unsupported computer action: ${action}`,
                };
        }
    }

    public async planAction(goal: string, additionalContext: string, additionalInstructions: string[],
        currentState: BrowserState, sessionHistory: BrowserStep[]): Promise<BrowserAction> {
        const systemPrompt = this.formatSystemPrompt(goal, additionalContext, additionalInstructions);
        const messages = await this.formatIntoMessages(goal, currentState, sessionHistory);
        const scaling = this.getScalingRatio({ x: currentState.width, y: currentState.height });

        const response = await this.client.beta.messages.create({
            model: "claude-3-5-sonnet-20241022",
            system: systemPrompt,
            max_tokens: 1024,
            tools: [
                {
                    type: "computer_20241022",
                    name: "computer",
                    display_width_px: currentState.width,
                    display_height_px: currentState.height,
                    display_number: 1
                },
                {
                    name: 'stop_browsing',
                    description:
                        'Call this function when you have achieved the goal of the task.',
                    input_schema: {
                        type: 'object',
                        properties: {
                            success: {
                                type: 'boolean',
                                description: 'Whether the task was successful',
                            },
                            error: {
                                type: 'string',
                                description: 'The error message if the task was not successful',
                            },
                        },
                        required: ['success'],
                    },
                },
            ],
            messages,
            betas: ["computer-use-2024-10-22"],
        });

        const action = this.parseAction(response, scaling, currentState);

        console.log(action);

        return action;
    }
}