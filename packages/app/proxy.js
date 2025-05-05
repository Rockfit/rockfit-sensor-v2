// proxy.js
const system = require('../../system.js');
const httpProxy = require('http-proxy');
const protobose = require('protobase');
const getLogger = protobose.getLogger;
const protonode = require('protonode');
const config = require('@my/config');
const fs = require('fs');
const mime = require('mime');
const { join } = require('path');

const setupProxyHandler = (name, subscribe, handle, server) => {
  const startTime = new Date().getTime();
  const logger = getLogger(name, config.getBaseConfig(name, process, protonode.getServiceToken()));
  const proxy = httpProxy.createProxyServer({
    ws: true,
    xfwd: true,
    proxyTimeout: 0
  });
  
  proxy.on('error', (err, req, res) => {
    if (startTime + 10000 > new Date().getTime()) {
      return;
    }
    logger.error({ err, url: req.url }, 'Proxy error occurred');

    if (res.writeHead) {
      res.writeHead(502, { 'Content-Type': 'text/plain' });
    }
    res.end('Bad Gateway: Unable to connect to upstream service');
  });

  server.on('upgrade', function (req, socket, head) {
    const resolver = system.services.find((resolver) => resolver.route(req));

    if (!resolver || resolver.name === name) {
        if(resolver.name === name && req.url.endsWith('/webpack-hmr')) {
            //let nextjs handle its own websocket
            return
        }
        console.log('No resolver found for WebSocket request: ' + req.url);
        socket.destroy();
        return;
    }

    console.log('Proxying WebSocket request for: ' + req.url + ' to: ' + resolver.route(req));

    proxy.ws(req, socket, head, { target: resolver.route(req) });
  });

  subscribe((req, res) => {
    if (req.url.startsWith('/public/')) {
      logger.trace({ url: req.url }, "Serving public file: " + req.url);
      const url = decodeURIComponent(req.url.replace(/\.\.\//g, ''));
      const isFullDev = process.env.FULL_DEV === '1';
      const prefixPath = isFullDev ? '../../data/' : '../../../../../data/'
      const filePath = join(prefixPath, url);
      if (!fs.existsSync(filePath)) {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
        return;
      }

      res.writeHead(200, { 'Content-Type': mime.getType(filePath) });
      fs.createReadStream(filePath).pipe(res);
      return;
    }

    //legacy urls redirector, to be removed in the future, but necessary for the transition
    if (
      (req.url.includes('/workspace/dev/') || req.url.includes('/workspace/prod/') ||
       req.url === '/workspace/dev' || req.url === '/workspace/prod') &&
      !req.url.includes('redirected=true')
    ) {
      const newUrl = req.url.replace('/workspace/dev/', '/workspace/').replace('/workspace/prod/', '/workspace/').replace('/workspace/dev', '/workspace').replace('/workspace/prod', '/workspace') + '?redirected=true';
      res.writeHead(301, { Location: newUrl });
      res.end();
      return;
    }

    const resolver = system.services.find((resolver) => resolver.route(req));

    if (!resolver || resolver.name === name) {
      // console.log('No resolver found for: ' + req.url);
      return handle(req, res);
    }

    // console.log('Resolving request for: ' + req.url + ' to: ' + resolver.route(req));

    logger.trace({
      url: req.url,
      target: resolver.route(req),
      ip: req.connection.remoteAddress,
      method: req.method
    }, "Proxying request for: " + req.url + " to: " + resolver.route(req) + " from: " + req.connection.remoteAddress + " method: " + req.method);

    proxy.web(req, res, { target: resolver.route(req) });
  });
};

module.exports = setupProxyHandler;