import net from 'net';
import aedes from 'aedes';
import { Agent } from '../src/Agent';
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import {MQTTProtocol} from '../src/protocols/mqtt';
import * as mqtt from 'mqtt';

const aedesInstance = new aedes();
aedesInstance.authenticate = function (client, username, password, callback) { callback(null, true); };

let paramsSchema;
let returnSchema;
let agent;
let server;
let mqttClient;

describe('MQTT Agents', () => {
  beforeAll(async () => {
    server = net.createServer((socket) => {
      aedesInstance.handle(socket);
    });

    server.listen(12346);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    mqttClient = mqtt.connect('mqtt://localhost:12346');
    await new Promise((resolve) => setTimeout(resolve, 1000));
    
    paramsSchema = z.object({
      id: z.string().uuid(),
      name: z.string().min(1),
      age: z.number().min(18),
      email: z.string().email(),
    });

    returnSchema = z.string();

    agent = new Agent({
      id: 'getDisplayInfo',
      name: 'getDisplayInfo',
      description: 'Get display info of a user',
      tags: ['user', 'display'],
      interface: {
        protocol: {
          type: 'mqtt',
          config: {
            serializer: 'json',
            encoder: 'body',
            topic: 'getDisplayInfo',
            url: 'mqtt://localhost:12346',
          },
        },
        input: {
          shape: zodToJsonSchema(paramsSchema, 'params'),
        },
      },
    });
  });

  afterAll(() => {
    server.close();
    aedesInstance.close();
  });

  it('Should be able to run the agent through mqtt', async () => {
    // Variables para almacenar el estado y el mensaje publicado
    let messagePublished = false;
    let publishedPayload = null;

    // Escuchar el evento 'publish' antes de ejecutar mqttRunner
    aedesInstance.on('publish', (packet, client) => {
      if (packet.topic === 'getDisplayInfo') {
        messagePublished = true;
        publishedPayload = packet.payload.toString();
      }
    });

    const payload = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      name: 'John Doe',
      age: 30,
      email: 'a@a.com',
    };
    const protocol = MQTTProtocol.create(agent, mqttClient);
    await protocol.send(payload);
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(messagePublished).toBe(true);
    expect(() => paramsSchema.parse(JSON.parse(publishedPayload))).not.toThrow();
  });
});