import { Key } from "selenium-webdriver";

export function parseXdotool(xdotoolCommand: string): { modifiers: string[], keys: string[] } {
    const modifiers: string[] = [];
    const keys: string[] = [];

    for (const keySequence of xdotoolCommand) {
        const keyParts = keySequence.split('+');

        for (const keyPart of keyParts) {
            switch (keyPart.toLowerCase()) {
                case 'ctrl':
                    modifiers.push(Key.CONTROL);
                    break;
                case 'alt':
                    modifiers.push(Key.ALT);
                    break;
                case 'shift':
                    modifiers.push(Key.SHIFT);
                    break;
                case 'super':
                case 'command':
                case 'meta':
                    modifiers.push(Key.META);
                    break;
                case 'null':
                    keys.push(Key.NULL);
                    break;
                case 'cancel':
                    keys.push(Key.CANCEL);
                    break;
                case 'help':
                    keys.push(Key.HELP);
                    break;
                case 'backspace':
                case 'back_space':
                    keys.push(Key.BACK_SPACE);
                    break;
                case 'tab':
                    keys.push(Key.TAB);
                    break;
                case 'clear':
                    keys.push(Key.CLEAR);
                    break;
                case 'return':
                case 'enter':
                    keys.push(Key.RETURN);
                    break;
                case 'pause':
                    keys.push(Key.PAUSE);
                    break;
                case 'escape':
                    keys.push(Key.ESCAPE);
                    break;
                case 'space':
                    keys.push(Key.SPACE);
                    break;
                case 'pageup':
                case 'page_up':
                    keys.push(Key.PAGE_UP);
                    break;
                case 'pagedown':
                case 'page_down':
                    keys.push(Key.PAGE_DOWN);
                    break;
                case 'end':
                    keys.push(Key.END);
                    break;
                case 'home':
                    keys.push(Key.HOME);
                    break;
                case 'left':
                case 'arrowleft':
                case 'arrow_left':
                    keys.push(Key.ARROW_LEFT);
                    break;
                case 'up':
                case 'arrowup':
                case 'arrow_up':
                    keys.push(Key.ARROW_UP);
                    break;
                case 'right':
                case 'arrowright':
                case 'arrow_right':
                    keys.push(Key.ARROW_RIGHT);
                    break;
                case 'down':
                case 'arrowdown':
                case 'arrow_down':
                    keys.push(Key.ARROW_DOWN);
                    break;
                case 'insert':
                    keys.push(Key.INSERT);
                    break;
                case 'delete':
                    keys.push(Key.DELETE);
                    break;
                case 'semicolon':
                    keys.push(Key.SEMICOLON);
                    break;
                case 'equals':
                    keys.push(Key.EQUALS);
                    break;
                case 'kp_0':
                    keys.push(Key.NUMPAD0);
                    break;
                case 'kp_1':
                    keys.push(Key.NUMPAD1);
                    break;
                case 'kp_2':
                    keys.push(Key.NUMPAD2);
                    break;
                case 'kp_3':
                    keys.push(Key.NUMPAD3);
                    break;
                case 'kp_4':
                    keys.push(Key.NUMPAD4);
                    break;
                case 'kp_5':
                    keys.push(Key.NUMPAD5);
                    break;
                case 'kp_6':
                    keys.push(Key.NUMPAD6);
                    break;
                case 'kp_7':
                    keys.push(Key.NUMPAD7);
                    break;
                case 'kp_8':
                    keys.push(Key.NUMPAD8);
                    break;
                case 'kp_9':
                    keys.push(Key.NUMPAD9);
                    break;
                case 'multiply':
                    keys.push(Key.MULTIPLY);
                    break;
                case 'add':
                    keys.push(Key.ADD);
                    break;
                case 'separator':
                    keys.push(Key.SEPARATOR);
                    break;
                case 'subtract':
                    keys.push(Key.SUBTRACT);
                    break;
                case 'decimal':
                    keys.push(Key.DECIMAL);
                    break;
                case 'divide':
                    keys.push(Key.DIVIDE);
                    break;
                case 'f1':
                    keys.push(Key.F1);
                    break;
                case 'f2':
                    keys.push(Key.F2);
                    break;
                case 'f3':
                    keys.push(Key.F3);
                    break;
                case 'f4':
                    keys.push(Key.F4);
                    break;
                case 'f5':
                    keys.push(Key.F5);
                    break;
                case 'f6':
                    keys.push(Key.F6);
                    break;
                case 'f7':
                    keys.push(Key.F7);
                    break;
                case 'f8':
                    keys.push(Key.F8);
                    break;
                case 'f9':
                    keys.push(Key.F9);
                    break;
                case 'f10':
                    keys.push(Key.F10);
                    break;
                case 'f11':
                    keys.push(Key.F11);
                    break;
                case 'f12':
                    keys.push(Key.F12);
                    break;
                default:
                    keys.push(keyPart);
            }
        }
    }

    return { modifiers, keys };
}