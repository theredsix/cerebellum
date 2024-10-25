import Anthropic from '@anthropic-ai/sdk';
import { ActionPlanner, BrowserAction, BrowserState, BrowserStep, Coordinate } from './browser';
import * as sharp from 'sharp';

const client = new Anthropic({
  apiKey: process.env['ANTHROPIC_API_KEY'], // This is the default and can be omitted
});

async function main() {
  const message = await client.messages.create({
    max_tokens: 1024,
    messages: [{ role: 'user', content: 'Hello, Claude' }],
    model: 'claude-3-opus-20240229',
  });

  console.log(message.content);
}

main();

interface ResizedImage {
    image: string;
    ratio: Coordinate;
    oldSize: Coordinate;
    newSize: Coordinate;
}

export class AnthropicPlanner extends ActionPlanner {
    private client: Anthropic;

    constructor(apiKey: string);
    constructor(client: Anthropic);

    constructor(apiKeyOrClient: string | Anthropic) {
        super();
        if (typeof apiKeyOrClient === 'string') {
            this.client = new Anthropic({ apiKey: apiKeyOrClient });
        } else {
            this.client = apiKeyOrClient;
        }
    }


    public async resizeScreenshot(screenshot: string): Promise<ResizedImage> {
        const sharpImage = sharp(screenshot);
        const originalMeta = await sharpImage.metadata();
        const resizedImg = await sharpImage.resize(1280, 800, {fit: 'inside'})
        
        const imgBuffer = await resizedImg.jpeg({quality: 90}).toBuffer();

        const resizedMeta = await sharp(imgBuffer).metadata();

        // Calculate the height and width ratio of the original to resized image
        const widthRatio = originalMeta.width! / resizedMeta.width!;
        const heightRatio = originalMeta.height! / resizedMeta.height!;

        const resizedImage: ResizedImage = {
            image: imgBuffer.toString('base64'),
            ratio: {
                x: widthRatio,
                y: heightRatio,
            },
            oldSize: {
                x: originalMeta.width!,
                y: originalMeta.height!
            },
            newSize: {
                x: resizedMeta.width,
                y: resizedMeta.height,
            }
        }

        return resizedImage;
    }

    public formatSystemPrompt(): string {
        const prompt = `<SYSTEM_CAPABILITY>
* You are utilizing a browser in fullscreen mode.
* You are provided with the browser's current URL in each step.
* The current date is ${new Date().toString()}.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""`;

        return prompt;

    }


    public async planAction(goal: string, additionalContext: string | undefined, 
        currentState: BrowserState, sessionHistory: BrowserStep[]): Promise<BrowserAction> {
        

        const message = await this.client.beta.messages.create({
                model: "claude-3-5-sonnet-20241022",
                max_tokens: 1024,
                tools: [
                    {
                      type: "computer_20241022",
                      name: "computer",
                      display_width_px: 1024,
                      display_height_px: 768,
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
                messages: [{ role: "user", content: "Save a picture of a cat to my desktop." }],
                betas: ["computer-use-2024-10-22"],
              });
    }
}