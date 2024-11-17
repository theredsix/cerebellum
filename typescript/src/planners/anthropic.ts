import Anthropic from '@anthropic-ai/sdk';
import { ActionPlanner, BrowserAction, BrowserState, BrowserStep, Coordinate, ScrollBar } from '../browser';
import sharp from 'sharp';
import { BetaContentBlockParam, BetaImageBlockParam, BetaMessageParam, BetaTextBlockParam } from '@anthropic-ai/sdk/resources/beta/messages/messages';

import fs from 'fs';
interface ScalingRatio {
    ratio: Coordinate;
    oldSize: Coordinate;
    newSize: Coordinate;
}

interface MsgOptions {
    mousePosition: boolean;
    screenshot: boolean;
    tabs: boolean;
}

const cursor64 = 'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAQCAYAAAAvf+5AAAAAw3pUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjabVBRDsMgCP33FDuC8ijF49i1S3aDHX9YcLFLX+ITeOSJpOPzfqVHBxVOvKwqVSQbuHKlZoFmRzu5ZD55rvX8Uk9Dz2Ql2A1PVaJ/1MvPwK9m0TIZ6TOE7SpUDn/9M4qH0CciC/YwqmEEcqGEQYsvSNV1/sJ25CvUTxqBjzGJU86rbW9f7B0QHSjIxoD6AOiHE1oXjAlqjQVyxmTMkJjEFnK3p4H0BSRiWUv/cuYLAAABhWlDQ1BJQ0MgcHJvZmlsZQAAeJx9kT1Iw0AYht+2SqVUHCwo0iFD1cWCqIijVqEIFUKt0KqDyaV/0KQhSXFxFFwLDv4sVh1cnHV1cBUEwR8QZwcnRRcp8buk0CLGg7t7eO97X+6+A/yNClPNrnFA1SwjnUwI2dyqEHxFCFEM0DoqMVOfE8UUPMfXPXx8v4vzLO+6P0evkjcZ4BOIZ5luWMQbxNObls55nzjCSpJCfE48ZtAFiR+5Lrv8xrnosJ9nRoxMep44QiwUO1juYFYyVOIp4piiapTvz7qscN7irFZqrHVP/sJwXltZ5jrNKJJYxBJECJBRQxkVWIjTrpFiIk3nCQ//kOMXySWTqwxGjgVUoUJy/OB/8Lu3ZmFywk0KJ4DuF9v+GAaCu0Czbtvfx7bdPAECz8CV1vZXG8DMJ+n1thY7Avq2gYvrtibvAZc7wOCTLhmSIwVo+gsF4P2MvikH9N8CoTW3b61znD4AGepV6gY4OARGipS97vHuns6+/VvT6t8Ph1lyr0hzlCAAAA14aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOjFiYzFkZjE3LWM5YmMtNGYzZi1hMmEzLTlmODkyNWNiZjY4OSIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo4YTUyMWJhMC00YmNlLTQzZWEtYjgyYS04ZGM2MTBjYmZlOTgiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplODQ3ZjUxNC00MWVlLTQ2ZjYtOTllNC1kNjI3MjMxMjhlZTIiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE3MzAxNTc3NjY5MTI3ODciCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zOCIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMjQ6MTA6MjhUMTY6MjI6NDYtMDc6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDI0OjEwOjI4VDE2OjIyOjQ2LTA3OjAwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZTVjOTM2ZDYtYjMzYi00NzM4LTlhNWUtYjM3YTA5MzdjZDAxIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyNC0xMC0yOFQxNjoyMjo0Ni0wNzowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz5/5aQ8AAAABmJLR0QAcgByAAAtJLTuAAAACXBIWXMAAABZAAAAWQGqnamGAAAAB3RJTUUH6AocFxYuv5vOJAAAAHhJREFUKM+NzzEOQXEMB+DPYDY5iEVMIpzDfRxC3mZyBK7gChZnELGohaR58f7a7dd8bVq4YaVQgTvWFVjCUcXxA28qcBBHFUcVRwWPPuFfXVsbt0PPnLBL+dKHL+wxxhSPhBcZznuDXYKH1uGzBJ+YtPAZRyy/jTd7qEoydWUQ7QAAAABJRU5ErkJggg==';
const cursorBuffer = Buffer.from(cursor64, 'base64');

export interface AnthropicPlannerOptions {
    screenshotHistory?: number;
    mouseJitterReduction?: number;
    apiKey?: string;
    client?: Anthropic;
    debugImagePath?: string;
}

export class AnthropicPlanner extends ActionPlanner {
    private client: Anthropic;
    private screenshotHistory: number = 1;
    private mouseJitterReduction: number = 5;
    private inputTokenUsage: number = 0;
    private outputTokenUsage: number = 0;
    private debugImagePath: string | undefined;
    private debug: boolean = false;

    constructor(options?: AnthropicPlannerOptions) {
        super();

        if (options?.client) {
            this.client = options.client;
        } else if (options?.apiKey) {
            this.client = new Anthropic({ apiKey: options.apiKey });
        } else {
            this.client = new Anthropic();
        }

        this.screenshotHistory = options?.screenshotHistory ?? this.screenshotHistory;
        this.mouseJitterReduction = options?.screenshotHistory ?? this.mouseJitterReduction;
        this.debugImagePath = options?.debugImagePath;
    }

    public formatSystemPrompt(goal: string, additionalContext: string, additionalInstructions: string[]): string {
        const prompt = `<SYSTEM_CAPABILITY>
* You are a computer use tool that is controlling a browser in fullscreen mode to complete a goal for the user. The goal is listed below in <USER_TASK>.
* The browser operates in fullscreen mode, meaning you cannot use standard browser UI elements like STOP, REFRESH, BACK, or the address bar. You must accomplish your task solely by interacting with the website's user interface or calling "switch_tab" or "stop_browsing"
* After each action, you will be provided with mouse position, open tabs, and a screenshot of the active browser tab.
* Use the Page_down or Page_up keys to scroll through the webpage. If the website is scrollable, a gray rectangle-shaped scrollbar will appear on the right edge of the screenshot. Ensure you have scrolled through the entire page before concluding that content is unavailable.
* The mouse cursor will appear as a black arrow in the screenshot. Use its position to confirm whether your mouse movement actions have been executed successfully. Ensure the cursor is correctly positioned over the intended UI element before executing a click command.
* After each action, you will receive information about open browser tabs. This information will be in the form of a list of JSON objects, each representing a browser tab with the following fields:
  - "tab_id": An integer that identifies the tab within the browser. Use this ID to switch between tabs.
  - "title": A string representing the title of the webpage loaded in the tab.
  - "active_tab": A boolean indicating whether this tab is currently active. You will receive a screenshot of the active tab.
  - "new_tab": A boolean indicating whether the tab was opened as a result of the last action.
* Follow all directions from the <IMPORTANT> section below. 
* The current date is ${new Date().toISOString()}.
</SYSTEM_CAPABILITY>

The user will ask you to perform a task and you should use their browser to do so. After each step, analyze the screenshot and carefully evaluate if you have achieved the right outcome. Explicitly show your thinking for EACH function call: "I have evaluated step X..." If not correct, try again. Only when you confirm a step was executed correctly should you move on to the next one. You should always call a tool! Always return a tool call. Remember call the stop_browsing tool when you have achieved the goal of the task. Use keyboard shortcuts to navigate whenever possible.

<IMPORTANT>
* After moving the mouse to the desired location, always perform a left-click to ensure the action is completed.
* You will use information provided in user's <USER DATA> to fill out forms on the way to your goal.
* Ensure that any UI element is completely visible on the screen before attempting to interact with it.
${additionalInstructions.map(instruction => `* ${instruction}`).join('\n')}
</IMPORTANT>`;
        
        return prompt.trim();
    }

    private createToolUseId(): string {
        const prefix = 'toolu_01';
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        const idLength = 22;
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

        // Set minimum size for image marking, otherwise return the original image
        if(width < 20 || height < 20){
            return imgBuffer;
        }
        
        // Create scrollbar overlay
        const scrollbarWidth = Math.min(10, width);
        const scrollbarHeight = Math.min(Math.floor(height * scrollbar.height), height);
        const scrollbarTop = Math.floor(height * scrollbar.offset);

        // Create a gray rectangle for the scrollbar
        const scrollbarBuffer = await sharp({
            create: {
                width: scrollbarWidth,
                height: scrollbarHeight,
                channels: 4,
                background: { r: 128, g: 128, b: 128, alpha: 0.7 }
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
            x: Math.min(Math.max(Math.floor(inputCoords.x / scaling.ratio.x), 1), scaling.newSize.x),
            y: Math.min(Math.max(Math.floor(inputCoords.y / scaling.ratio.y), 1), scaling.newSize.y),
        };
    }

    private llmToBrowserCoordinates(inputCoords: Coordinate, scaling: ScalingRatio): Coordinate {
        return {
            x: Math.min(Math.max(Math.floor(inputCoords.x * scaling.ratio.x), 1), scaling.oldSize.x),
            y: Math.min(Math.max(Math.floor(inputCoords.y * scaling.ratio.y), 1), scaling.oldSize.y),
        };
    }

    public async formatStateIntoMsg(toolCallId: string, currentState: BrowserState, options: MsgOptions): Promise<BetaMessageParam> {
        let resultText: string = '';
        const contentSubMsg: (BetaTextBlockParam | BetaImageBlockParam)[] = [];

        if (options.mousePosition) {
            const imgDim = { x: currentState.width, y: currentState.height };
            const scaling = this.getScalingRatio(imgDim);
            const scaledCoord = this.browserToLLMCoordinates(currentState.mouse, scaling);
            resultText += `Mouse location: ${JSON.stringify(scaledCoord)}\n\n`;
        }

        if (options.tabs) {
            const tabsAsDicts = currentState.tabs.map(tab => ({
                tab_id: tab.id,
                title: tab.title,
                active_tab: tab.active,
                new_tab: tab.new,
            }));
            resultText += `\n\nOpen Browser Tabs: ${JSON.stringify(tabsAsDicts)}\n\n`;
        }

        if (options.screenshot) {
            const imgBuffer = Buffer.from(currentState.screenshot, 'base64');
            const viewportImage = await this.resizeImageToDimensions(imgBuffer, { x: currentState.width, y: currentState.height });
            const markedImage = await this.markScreenshot(viewportImage, currentState.mouse, currentState.scrollbar);
            const resized = await this.resizeScreenshot(markedImage);

            if (this.debugImagePath) {
                fs.writeFileSync(this.debugImagePath, resized, 'base64');
            }

            contentSubMsg.push({
                type: 'image',
                source: {
                    type: 'base64',
                    media_type: 'image/png',
                    data: resized.toString('base64')
                }
            });
        }

        if (!resultText) { // Put a generic text explanation for no URL or result
            resultText = 'Action was performed.';
        }

        contentSubMsg.unshift({
            type: 'text',
            text: resultText.trim()
        });

        return {
            role: 'user',
            content: [
                {
                    type: 'tool_result',
                    tool_use_id: toolCallId,
                    content: contentSubMsg
                }
            ]
        };
    }

    public flattenBrowserStepToAction(step: BrowserStep): Record<string, any> {
        if (step.action.action === 'scroll_down') {
            return {
                action: 'key',
                text: 'Page_Down'
            };
        }

        if (step.action.action === 'scroll_up') {
            return {
                action: 'key',
                text: 'Page_Up'
            };
        }

        const val: Record<string, any> = {
            action: step.action.action,
        };

        if (step.action.text) {
            val.text = step.action.text;
        }

        if (step.action.coordinate) {
            const imgDim:  Coordinate = { x: step.state.width, y: step.state.height};
            const scaling = this.getScalingRatio(imgDim);
            const llmCoordinates = this.browserToLLMCoordinates(
                {x: step.action.coordinate[0], y: step.action.coordinate[1]}, scaling);
            val.coordinate = [llmCoordinates.x, llmCoordinates.y];
        }

        return val;
    }

    public async formatIntoMessages(goal: string, additionalContext: string, currentState: BrowserState, sessionHistory: BrowserStep[]): Promise<BetaMessageParam[]> {
        const messages: BetaMessageParam[] = [];

        let toolId = this.createToolUseId();

        const user_prompt =`Please complete the following task:
<USER_TASK>
${goal}
</USER_TASK>

Using the supporting contextual data:
<USER_DATA>
${additionalContext}
</USER_DATA>
`;

        const msg0: BetaMessageParam = { role: 'user', content: [{ type: 'text', text: user_prompt.trim() }] };
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
                tabs: true,
            }

            if (pastStepIdx <= (sessionHistory.length - this.screenshotHistory)) {
                options.tabs = false;
            }

            const resultMsg: BetaMessageParam = await this.formatStateIntoMsg(toolId, pastStep.state, options)

            messages.push(resultMsg);
            // Update the tool use id as now we're going to pretend to get the response
            toolId = pastStep.action.id ?? this.createToolUseId();

            const actionMsg: BetaMessageParam = {
                role: 'assistant',
                content: [
                    {
                        type: 'tool_use',
                        id: toolId,
                        name: 'computer',
                        input: this.flattenBrowserStepToAction(pastStep)
                    }
                ]
            }

            messages.push(actionMsg);
        }

        const currentStateMessage: BetaMessageParam = await this.formatStateIntoMsg(toolId, currentState, { mousePosition: true, screenshot: true, tabs: true });
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
                reasoning: lastMessage,
                id: this.createToolUseId()
            };
        }

        if (lastMessage.type !== 'tool_use') {
            return {
                action: 'failure',
                reasoning,
                id: this.createToolUseId()
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
                    text: input.error ?? 'Unknown error',
                    id: lastMessage.id
                };
            }
            return {
                action: 'success',
                reasoning,
                text: input.error ?? 'Unknown error',
                id: lastMessage.id
            };
        }
        if (lastMessage.name !== 'computer') {
            return {
                action: 'failure',
                reasoning,
                text: 'Wrong message called',
                id: lastMessage.id
            };
        }

        const { action, text } = lastMessage.input as {
            action: string;            
            text?: string;
        };

        let coordinate: [number, number] | undefined;
        let rawCoord = (lastMessage.input as any).coordinate;

        // If we get coordinates as string
        if (typeof rawCoord == 'string') {
            console.log('Coordinate is a string:', rawCoord);
            rawCoord = JSON.parse(rawCoord);
        } 
        
        // Parse the coordinate object
        if (typeof rawCoord == 'object'){
            if ('x' in rawCoord && 'y' in rawCoord){
                console.log('Coordinate object has x and y properties');
                coordinate = [rawCoord.x, rawCoord.y]
            } else if (Array.isArray(rawCoord)) {
                coordinate = [rawCoord[0], rawCoord[1]];
            }
        }

        switch (action) {
            case 'key':
                // Treat scrolling actions in a special manner
                if (['page_down', 'pagedown'].includes(text?.toLocaleLowerCase().trim() ?? '')) {
                    return {
                        action: 'scroll_down',
                        reasoning,
                        id: lastMessage.id
                    }
                } else if (['page_up', 'pageup'].includes(text?.toLocaleLowerCase().trim() ?? '')) {
                    return {
                        action: 'scroll_up',
                        reasoning,
                        id: lastMessage.id
                    }
                }
                // Explicit fallthrough
            case 'type':
                if (!text) {
                    return {
                        action: 'failure',
                        reasoning,
                        text: `No text provided for ${action}`,
                        id: lastMessage.id
                    };
                } else {
                    return {
                        action,
                        reasoning,
                        text,
                        id: lastMessage.id
                    }
                }
            case 'mouse_move':
                if (!coordinate) {
                    return { 
                        action: 'failure', 
                        reasoning, 
                        text: 'No coordinate provided',
                        id: lastMessage.id
                    };
                } else {
                    // Scale back coordinates
                    const browserCoordinates = this.llmToBrowserCoordinates({x: coordinate[0], y: coordinate[1]}, scaling);

                    const xJitter = Math.abs(browserCoordinates.x - currentState.mouse.x);
                    const yJitter = Math.abs(browserCoordinates.y - currentState.mouse.y);
                    // Check if the browser coordinates match the current mouse position
                    if (xJitter <= this.mouseJitterReduction && yJitter <= this.mouseJitterReduction) {
                        console.log('Mouse jitter detected, overriding with click');
                        // If coordinates match, dispatch a click event instead of moving the mouse
                        return { 
                            action: 'left_click', 
                            reasoning,
                            id: lastMessage.id
                        };
                    }
                }
            case 'left_click_drag':
                if (!coordinate) {
                    return { 
                        action: 'failure', 
                        reasoning, 
                        text: 'No coordinate provided',
                        id: lastMessage.id
                    };
                } else {
                    // Scale back coordinates
                    const browserCoordinates = this.llmToBrowserCoordinates({x: coordinate[0], y: coordinate[1]}, scaling);
                    
                    return { 
                        action, 
                        reasoning, 
                        coordinate: [browserCoordinates.x, browserCoordinates.y],
                        id: lastMessage.id
                    };
                }
            case 'switch_tab':
                const tabId = parseInt(text ?? '', 10);
                if (isNaN(tabId)) {
                    return {
                        action: 'failure',
                        reasoning,
                        text: 'Invalid tab ID provided for switch_tab',
                        id: lastMessage.id
                    };
                }
                return {
                    action: 'switch_tab',
                    reasoning,
                    text,
                    id: lastMessage.id
                };
            case 'left_click':
            case 'right_click':
            case 'middle_click':
            case 'double_click':
            case 'screenshot':
            case 'cursor_position':
                return { 
                    action, 
                    reasoning,
                    id: lastMessage.id 
                };
            default:
                return {
                    action: 'failure',
                    reasoning,
                    text: `Unsupported computer action: ${action}`,
                    id: lastMessage.id
                };
        }
    }

    public async planAction(goal: string, additionalContext: string, additionalInstructions: string[],
        currentState: BrowserState, sessionHistory: BrowserStep[]): Promise<BrowserAction> {
        const systemPrompt = this.formatSystemPrompt(goal, additionalContext, additionalInstructions);
        const messages = await this.formatIntoMessages(goal, additionalContext, currentState, sessionHistory);
        const scaling = this.getScalingRatio({ x: currentState.width, y: currentState.height });

        this.printMessagesWithoutScreenshots(messages);

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
                    name: 'switch_tab',
                    description: 'Call this function to switch the active browser tab to a new one',
                    input_schema: {
                        type: 'object',
                        properties: {
                            tab_id: {
                                type: 'integer',
                                description: 'The ID of the tab to switch to',
                            },
                        },
                        required: ['tab_id'],
                    },
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

        console.log(`Token usage - Input: ${response.usage.input_tokens}, Output: ${response.usage.output_tokens}`);
        this.inputTokenUsage += response.usage.input_tokens;
        this.outputTokenUsage += response.usage.output_tokens;
        console.log(`Cumulative token usage - Input: ${this.inputTokenUsage}, Output: ${this.outputTokenUsage}, Total: ${this.inputTokenUsage + this.outputTokenUsage}`);

        const action = this.parseAction(response, scaling, currentState);
        console.log(action);

        return action;
    }

public printMessagesWithoutScreenshots(msg: BetaMessageParam[]): void {
    // Create a deep copy of the messages to avoid modifying the original
    const msgCopy: BetaMessageParam[] = JSON.parse(JSON.stringify(msg));

    // Iterate over each message in the copy
    for (const message of msgCopy) {
        if (message.content) {
            for (const outerContent of message.content as any) {
                if (outerContent.content) {
                    // Filter out any content of type 'image'
                    outerContent.content = outerContent.content.filter((content: BetaContentBlockParam) => content.type !== 'image');
                }
            }
        }
    }

    // Print each message in the modified copy
    for (const message of msgCopy) {
        console.log(JSON.stringify(message, null, 2));
    }
}
}