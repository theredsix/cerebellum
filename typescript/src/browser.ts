import { WebDriver, Origin } from "selenium-webdriver";
import { parseXdotool, pauseForInput } from './util';

export type BrowserGoalState = 'initial' | 'running' | 'success' | 'failed';

export interface BrowserState {
    screenshot: string;
    height: number;
    width: number;
    scrollbar: ScrollBar;
    tabs: BrowserTab[];
    active_tab: string;
    mouse: Coordinate;
}

export interface ScrollBar {
    offset: number;
    height: number;
}

export interface BrowserTab {
    handle: string;
    url: string;
    title: string;
    active: boolean;
    new: boolean;
    id: number;
}

export interface BrowserAction {
    action: "success" | "failure" | "key" | "type" | "mouse_move" | "left_click" | "left_click_drag" |
    "right_click" | "middle_click" | "double_click" | "screenshot" | "cursor_position" | "scroll_up" | 
    "scroll_down" | "switch_tab";
    coordinate?: [number, number];
    text?: string;
    reasoning: string;
    id: string;
}

export interface BrowserStep {
    state: BrowserState;
    action: BrowserAction;
}

export interface Coordinate {
    x: number;
    y: number;
}

export abstract class ActionPlanner {
    public abstract planAction(goal: string, additionalContext: string, additionalInstructions: string[],
        currentState: BrowserState, sessionHistory: BrowserStep[]): Promise<BrowserAction>;
}

export interface BrowserAgentOptions {
    additionalContext?: string | Record<string, any>;
    additionalInstructions?: string[];
    waitAfterStepMS?: number;
    pauseAfterEachAction?: boolean;
    maxSteps?: number;
}

export class BrowserAgent {
    public readonly driver: WebDriver;
    public readonly planner: ActionPlanner;
    public readonly goal: string;
    public additionalContext: string = "None";
    public additionalInstructions: string[] = [];
    public waitAfterStepMS: number = 500;
    public pauseAfterEachAction: boolean = false;
    public maxSteps: number = 50;
    private _status: BrowserGoalState = 'initial';
    public readonly history: BrowserStep[] = [];
    public tabs: Record<string, BrowserTab> = {};

    constructor(driver: WebDriver, actionPlanner: ActionPlanner, goal: string, options?: BrowserAgentOptions) {
        this.driver = driver;
        this.planner = actionPlanner;
        this.goal = goal;

        if (options) {
            if (options.additionalContext !== undefined) {
                if (typeof options.additionalContext !== "string") {
                    this.additionalContext = JSON.stringify(options.additionalContext);
                } else {
                    this.additionalContext = options.additionalContext;
                }
            }
            if (options.additionalInstructions !== undefined) {
                this.additionalInstructions = options.additionalInstructions;
            }
            if (options.waitAfterStepMS !== undefined) {
                this.waitAfterStepMS = options.waitAfterStepMS;
            }
            if (options.pauseAfterEachAction !== undefined) {
                this.pauseAfterEachAction = options.pauseAfterEachAction;
            }
            if (options.maxSteps !== undefined) {
                this.maxSteps = options.maxSteps;
            }
        }
    }

    public async getState(): Promise<BrowserState> {
        const size = await this.driver.executeScript('return { x: window.innerWidth, y: window.innerHeight }') as Coordinate;
        const screenshot = await this.driver.takeScreenshot();
        const mousePosition = await this.getMousePosition();
        const scrollPosition = await this.getScrollPosition();

        const tabs = await this.driver.getAllWindowHandles();
        const currentTab = await this.driver.getWindowHandle();
        const browserTabs: BrowserTab[] = [];

        for (const tab of tabs) {
            await this.driver.switchTo().window(tab);
            const tabUrl = await this.driver.getCurrentUrl();
            const tabTitle = await this.driver.getTitle();
            const isActive = tab === currentTab;

            let tabId: number;
            let isNew: boolean;
            if (this.tabs[tab]) {
                tabId = this.tabs[tab].id;
                isNew = false;
            } else {
                tabId = Object.keys(this.tabs).length;
                isNew = true;
            }

            const browserTab: BrowserTab = {
                handle: tab,
                url: tabUrl,
                title: tabTitle,
                active: isActive,
                new: isNew,
                id: tabId,
            };

            this.tabs[tab] = browserTab;
            browserTabs.push(browserTab);
        }

        await this.driver.switchTo().window(currentTab);

        return {
            screenshot: screenshot,
            height: size.y,
            width: size.x,
            scrollbar: scrollPosition,
            tabs: browserTabs,
            active_tab: currentTab,
            mouse: mousePosition,
        };
    }

    public async getAction(currentState: BrowserState): Promise<BrowserAction> {
        return await this.planner.planAction(this.goal, this.additionalContext, this.additionalInstructions, currentState, this.history);
    }

    public async getScrollPosition(): Promise<ScrollBar> {
        const [offset, height] = (await this.driver.executeScript('return [window.pageYOffset/document.documentElement.scrollHeight , window.innerHeight/document.documentElement.scrollHeight]')) as [number, number];
        
        return {
            height,
            offset,
        };
    }

    public async getMousePosition(): Promise<Coordinate> {
        const listenScript = `
        window.last_mouse_x = 0;
        window.last_mouse_y = 0;
        window.addEventListener('mousemove', function onMouseMove(ev) {
            window.last_mouse_x = ev.clientX;
            window.last_mouse_y = ev.clientY;
            window.removeEventListener('mousemove', onMouseMove);
        });`;

        await this.driver.executeScript(listenScript);

        await this.driver.actions().move({x: 3, y: 3, origin: Origin.POINTER}).perform();
        await this.driver.actions().move({x: -3, y: -3, origin: Origin.POINTER}).perform();
        
        await new Promise(resolve => setTimeout(resolve, 100));

        const [x, y] = (await this.driver.executeScript('return [window.last_mouse_x, window.last_mouse_y]')) as [number, number];

        if (typeof x === 'number' && typeof y === 'number') {
            return { x, y };
        }

        return { x: 0, y: 0 };
    }

    public async takeAction(action: BrowserAction, lastState: BrowserState): Promise<void> {
        const actions = this.driver.actions({ async: true });

        switch (action.action) {
            case 'key':
                if (!action.text) throw new Error('Text is required for key action');

                const parsedKeyStrokes = parseXdotool(action.text);
                let keyAction = actions;
                for (const modifier of parsedKeyStrokes.modifiers) {
                    keyAction = keyAction.keyDown(modifier);
                }
                for (const key of parsedKeyStrokes.keys) {
                    keyAction = keyAction.sendKeys(key);
                }
                for (const modifier of parsedKeyStrokes.modifiers.reverse()) {
                    keyAction = keyAction.keyUp(modifier);
                }
                await keyAction.perform();
                break;
            case 'type':
                if (!action.text) throw new Error('Text is required for type action');
                await actions.sendKeys(action.text).perform();
                break;
            case 'mouse_move':
                if (!action.coordinate) throw new Error('Coordinate is required for mouse_move action');
                await actions.move({ x: action.coordinate[0], y: action.coordinate[1] }).perform();
                break;
            case 'left_click':
                await actions.click().perform();
                break;
            case 'left_click_drag':
                if (!action.coordinate) throw new Error('Coordinate is required for left_click_drag action');
                await actions.press().move({ x: action.coordinate[0], y: action.coordinate[1] }).release().perform();
                break;
            case 'right_click':
                await actions.contextClick().perform();
                break;
            case 'middle_click':
                console.log('Middle mouse click not supported');
                break;
            case 'double_click':
                await actions.doubleClick().perform();
                break;
            case 'screenshot':
            case 'cursor_position':
                break;
            case 'scroll_down':
                await this.driver.executeScript(`window.scrollBy(0, ${lastState.height / 2})`);
                break;
            case 'scroll_up':
                await this.driver.executeScript(`window.scrollBy(0, -${lastState.height / 2})`);
                break;
            case 'switch_tab':
                if (!action.text) throw new Error('Text is required for switch_tab action');
                const targetId = parseInt(action.text);
                const tabHandle = Object.keys(this.tabs).find(handle => this.tabs[handle].id === targetId);
                if (!tabHandle) throw new Error(`No tab found with id: ${action.text}`);
                await this.driver.switchTo().window(tabHandle);
                break;
            default:
                throw new Error(`Unsupported action: ${action.action}`);
        }
    }

    public async step(): Promise<void> {
        const currentState = await this.getState();
        const nextAction = await this.getAction(currentState);

        if (nextAction.action === 'success') {
            this._status = 'success';
            return;
        } else if (nextAction.action === 'failure') {
            this._status = 'failed';
            return;
        } else {
            this._status = 'running';
            await this.takeAction(nextAction, currentState);
        }

        this.history.push({
            state: currentState,
            action: nextAction,
        });
    }

    public async start(): Promise<void> {
        await this.driver.actions().move({ x: 1, y: 1, origin: Origin.VIEWPORT }).perform();

        while (['initial', 'running'].includes(this._status) && this.history.length <= this.maxSteps) {
            await this.step();
            await this.driver.sleep(this.waitAfterStepMS);

            if (this.pauseAfterEachAction) {
                await pauseForInput();
            }
        }
    }

    public get status(): string {
        return this._status;
    }
}