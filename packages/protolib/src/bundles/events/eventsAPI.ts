import { EventModel } from ".";
import { AutoAPI, getDBOptions, getServiceToken } from 'protonode'
import { connectDB, getDB } from '@my/config/dist/storageProviders';
import { API } from 'protobase'

export const EventsAPI = async (app, context) => {
    const EventAPI = AutoAPI({
        modelName: 'events',
        modelType: EventModel,
        prefix: '/api/core/v1/',
        skipStorage: async(data,session?,req?) => {
            if(data.ephemeral){
                return true
            }
            return false
        },
        dbName: 'events',
        notify: (entityModel, action) => {
            context.mqtt.publish(entityModel.getNotificationsTopic(action), entityModel.getNotificationsPayload())
        },
        disableEvents: true,
        requiresAdmin: ['*'],
        itemsPerPage: 50,
        logLevel: "trace",
        defaultOrderBy: 'created',
        defaultOrderDirection: 'desc',
        dbOptions: {
            orderedInsert: true,
            maxEntries: parseInt(process.env.MAX_EVENTS, 10) || 100000
        }
    })
    EventAPI(app, context)
}
