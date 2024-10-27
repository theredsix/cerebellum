import Anthropic from '@anthropic-ai/sdk';
import { ActionPlanner, BrowserAction, BrowserState, BrowserStep, Coordinate } from '../browser';
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

const cursor64 = 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABjSURBVDiNY2bAD6oYGBhsGBgYjuBSwELAAHEC8gxMhBSMAAMIBeJHYgyoZWBgkMEi94aBgaEOym5jYGAQxqLmMRMDA8N/QrbgUUNQbxMU4wSEwoCfkA0DH40DbwChQHxByAAAyEkLI/q5QTQAAAAASUVORK5CYII=';
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

    public async markScreenshotWithCursor(screenshot: string, mousePosition: Coordinate): Promise<string> {
        const imgBuffer = Buffer.from(screenshot, 'base64');
        const sharpImage = sharp(imgBuffer);

        // Create a red circle for the cursor
        const cursorSize = 16;

        // Overlay the cursor on the screenshot
        const markedImage = await sharpImage.composite([{
            input: cursorBuffer,
            top: Math.max(0, mousePosition.y - cursorSize / 2),
            left: Math.max(0, mousePosition.x - cursorSize / 2)
        }]);

        // Convert the image back to base64
        const outputBuffer = await markedImage.toBuffer();
        return outputBuffer.toString('base64');
    }

    public async resizeScreenshot(screenshot: string): Promise<string> {
        const screenshotBuffer =  Buffer.from(screenshot, 'base64');
        const sharpImage = sharp(screenshotBuffer);
        const resizedImg = await sharpImage.resize(1280, 800, { fit: 'inside' });
        const imgBuffer = await resizedImg.toBuffer();

        const imgStr = imgBuffer.toString('base64');
        return imgStr;
    }

    public async resizeImageToDimensions(image: string, newDim: Coordinate): Promise<string> {
        const screenshotBuffer =  Buffer.from(image, 'base64');
        const sharpImage = sharp(screenshotBuffer);
        const resizedImg = await sharpImage.resize(newDim.x, newDim.y, { fit: 'fill' });
        const imgBuffer = await resizedImg.toBuffer();

        const imgStr = imgBuffer.toString('base64');
        return imgStr;
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
            resultText += `After action mouse cursor is at X: ${scaledCoord.x}, Y: ${scaledCoord.y}\n\n`;
        }

        if (options.url) {
            resultText += `After action, the tab's URL is ${currentState.url}\n\n`;
        }

        if (options.screenshot) {
            resultText += 'Here is a screenshot of the browswer after the action was performed.\n\n';
            const viewportImage = await this.resizeImageToDimensions(currentState.screenshot, {x: currentState.width, y: currentState.height});
            const markedImage = await this.markScreenshotWithCursor(viewportImage, currentState.mouse);
            const resized = await this.resizeScreenshot(markedImage);
           
            fs.writeFileSync('tmp.png', resized, 'base64');
                        
            contentSubMsg.push({
                type: 'image',
                source: {
                    type: 'base64',
                    media_type: 'image/png',
                    data: resized
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
            case 'type':
            case 'key':
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