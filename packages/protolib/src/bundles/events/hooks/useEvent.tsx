import { useSubscription } from '../../../lib/mqtt'

export const useEvent = (eventFilter) => {
    const { message } = useSubscription('notifications/event/create/' + (eventFilter?.path && eventFilter.path))

    if (message && message.message && eventFilter) {
        try {
            let content = JSON.parse(message.message as string)
            if (eventFilter.from && content['from'] != eventFilter.from) {
                return
            }
            if (eventFilter.user && content['user'] != eventFilter.user) {
                return
            }
            return message;

        } catch (e) {
            console.error('Error parsing message from mqtt: ', e)
        }
    }

    return message
}