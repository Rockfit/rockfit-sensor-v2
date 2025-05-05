import { getLogger } from 'protobase';
import { chromium, firefox, webkit } from 'playwright'; 

const logger = getLogger();

export const getText = async (options: {
    element?: any,
    onDone?: (html) => void,
    onError?: (err) => void
}) => {
    const element = options.element

    if(!element) {
        throw new Error("GetText: element is required");
    }

    const onDone = options.onDone || (() => {});
    const onError = options.onError

    try {
        const result = await element.textContent()
        onDone(result);
        return result
    } catch (err) {
        if(onError) {
            onError(err);
        } else {
            throw new Error("Error in GetText: "+err.message);
        }
    }
}