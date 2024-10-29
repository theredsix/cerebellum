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

export interface AnthropicPlannerOptions {
    screenshotHistory: number;
    mouseJitterReduction: number;
}

export class AnthropicPlanner extends ActionPlanner {
    private client: Anthropic;
    private screenshotHistory: number = 1;
    private mouseJitterReduction: number = 5;
    private inputTokenUsage: number = 0;
    private outputTokenUsage: number = 0;

    constructor(_none: undefined);
    constructor(apiKey: string);
    constructor(client: Anthropic);

    constructor(apiKeyOrClient: undefined | string | Anthropic, options?: AnthropicPlannerOptions) {
        super();
        if (typeof apiKeyOrClient === 'string') {
            this.client = new Anthropic({ apiKey: apiKeyOrClient });
        } else if (typeof apiKeyOrClient === 'undefined') {
            this.client = new Anthropic();
        } else {
            this.client = apiKeyOrClient;
        }

        this.screenshotHistory = options?.screenshotHistory ?? this.screenshotHistory;
        this.mouseJitterReduction = options?.screenshotHistory ?? this.mouseJitterReduction;
    }

    public formatSystemPrompt(goal: string, additionalContext: string, additionalInstructions: string[]): string {
        const prompt = `<SYSTEM_CAPABILITY>
* You are a computer use tool that is controlling a browser in fullscreen mode to complete a goal for the user. The goal is listed below in <USER_TASK>.
* Since the browser is in fullscreen mode, you do not have access to browser UI elements such as STOP, REFRESH, BACK or the address bar. You will need to complete your task purely by interacting with the webside's UI.
* When viewing a page it can be helpful to zoom out so that you can see everything on the page. Either that, or make sure you scroll down to see everything before deciding something isn't available.
* ONLY use the Page_down or Page_up keys to scroll.
* If the website is scrollable, a scrollbar that is shaped like a gray rectangle will be visible on the right edge of the screenshot.
* The current date is ${new Date().toString()}.
* Follow all directions from the <IMPORTANT> section below. 
</SYSTEM_CAPABILITY>

The user will ask you to perform a task and you should use their browser to do so. After each step, take a screenshot and carefully evaluate if you have achieved the right outcome. Explicitly show your thinking for EACH function call: "I have evaluated step X..." If not correct, try again. Only when you confirm a step was executed correctly should you move on to the next one. You should always call a tool! Always return a tool call. Remember call the stop_browsing tool when you have achieved the goal of the task. Use keyboard shortcuts to navigate whenever possible.

<IMPORTANT>
* You will use information provided in user's <USER DATA> to fill out forms on the way to your goal.
* Always scroll a UI element fully into view before interacting with it.
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

        console.log('Generated fake id:', result);

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
                url: true,
            }

            if (pastStepIdx <= (sessionHistory.length - this.screenshotHistory)) {
                options.url = true;
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

        const { action, coordinate, text } = lastMessage.input as {
            action: string;
            coordinate?: [number, number];
            text?: string;
        };

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

        console.log(response);
        console.log(`Token usage - Input: ${response.usage.input_tokens}, Output: ${response.usage.output_tokens}`);
        this.inputTokenUsage += response.usage.input_tokens;
        this.outputTokenUsage += response.usage.output_tokens;
        console.log(`Cumulative token usage - Input: ${this.inputTokenUsage}, Output: ${this.outputTokenUsage}, Total: ${this.inputTokenUsage + this.outputTokenUsage}`);

        const action = this.parseAction(response, scaling, currentState);

        console.log(action);

        return action;
    }
}