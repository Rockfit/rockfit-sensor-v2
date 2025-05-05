import express from 'express';
import cookieParser from 'cookie-parser';
import cors from 'cors';
import httpLogger from "pino-http";
import { getConfig, getLogger, hasPermission } from 'protobase';
import { handler } from './handler'
import listEndpoints from "express-list-endpoints";
let app;

export const getApp = () => {
    if(!app) {
        const logger = getLogger()
        const config = getConfig()
        app = express();
        app.use(cors());
        app.use(cookieParser());
        app.use(express.json({ limit: '50mb' }));
        app.use(httpLogger({
            customSuccessMessage: function (req:any, res) {
                return `${req.method} ${req.originalUrl} - ${res.statusCode}`;
            },
            serializers: {
                req: (req) => {
                    if (process.env.NODE_ENV === "development") {
                        return {
                            method: req.method,
                            url: req.url,
                        };
                    } else {
                        return req;
                    }
                },
                res: (res) => {
                    if (process.env.NODE_ENV === "development") {
                        return {
                            code: res.statusCode,
                        };
                    } else {
                        return res;
                    }
                },
            },
        
            ...config.logger,
            useLevel: 'trace'
        }))
        
        app.get(global.defaultRoute+'/endpoints', handler(async (req, res, session, next) => {
            hasPermission(session, 'admin/endpoints/list')
            res.send(listEndpoints(app))
        }))
        
        logger.debug({route: global.defaultRoute}, "Default route: "+global.defaultRoute)
    }

    return app
}

