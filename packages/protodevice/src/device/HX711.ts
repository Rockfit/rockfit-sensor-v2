import { extractComponent } from "./utils"
class HX711 {
    name;
    type;
    platform;
    clkPin;
    updateInterval;
    gain;
    sensitivityBig;
    sensitivitySmall;
    smallThrottle;
    heartbeat;
    constructor(name, platform, clkPin, gain, updateInterval, sensitivityBig, sensitivitySmall, smallThrottle, heartbeat) {
        this.type = "sensor"
        this.name = name
        this.platform = platform
        this.clkPin = clkPin
        this.updateInterval = updateInterval
        this.gain = gain
        this.sensitivityBig = sensitivityBig
        this.sensitivitySmall = sensitivitySmall
        this.smallThrottle = smallThrottle
        this.heartbeat = heartbeat
    }
    attach(pin, deviceComponents) {
        const componentObjects = [
          {
            name: this.type,
            config: {
              platform: "template",
              name: this.name,
              id: this.name,
              update_interval: this.updateInterval,      
              filters: [
                {
                  or: [
                    { delta: this.sensitivityBig },
                    { heartbeat: this.heartbeat }
                  ]
                },
                {
                  or: [
                    { delta: this.sensitivitySmall },
                    { throttle: this.smallThrottle }
                  ]
                }
              ]  
            },
            subsystem: this.getSubsystem()
          },
          {
            name: this.type,
            config: {
              platform: this.platform,
              id: this.name+"_internal",
              dout_pin: pin,
              clk_pin: this.clkPin,
              gain: this.gain,
              update_interval: this.updateInterval,      
              on_raw_value:{
                then: {
                  lambda:
`id(${this.name}).publish_state(x);
`,
                }
              },
              on_value:{
                then: {
                  lambda:
`float delta = x - id(last_loadcell_value);
if (delta > ${this.sensitivityBig} ) {
  ESP_LOGD("LOADCELL", "Positive delta over ${this.sensitivityBig} : %.0f", delta);
  ESP_LOGD("LOADCELL", "last_loadcell_value = %f, current_value = %f", id(last_loadcell_value), x);
  id(handle_led_action).execute();
}

id(last_loadcell_value) = x;
`
                }
              }
            },
          },
          {
            name: 'mqtt',
            config: {
              on_message: [
                {
                  topic: `devices/${deviceComponents.esphome.name}/on_weight_action`,
                  then: [
                    {
                      lambda:
`json::parse_json(x.c_str(), [&](JsonObject root) -> bool {
  if (root.containsKey("action")) {
    std::string action = root["action"].as<std::string>();
    id(led_action) = action;

    float r = 1.0, g = 1.0, b = 1.0;
    int on_time = 200;

    if (root.containsKey("config")) {
      JsonObject config = root["config"];
      if (config.containsKey("r")) r = config["r"].as<float>();
      if (config.containsKey("g")) g = config["g"].as<float>();
      if (config.containsKey("b")) b = config["b"].as<float>();
      if (config.containsKey("on_time")) on_time = config["on_time"].as<int>();
    }

    id(led_r) = r;
    id(led_g) = g;
    id(led_b) = b;
    id(led_on_time) = on_time;

    ESP_LOGD("LED_CONTROL", "Parsed action: %s | r=%.2f g=%.2f b=%.2f on_time=%dms",
            id(led_action).c_str(), r, g, b, on_time);

    return false;
  }
  return true;
});
`
                    }
                  ]
                }
              ]
            }
          },
          {
            name: "globals",
            config:{
              id: "led_action",
              type: "std::string",
              initial_value: '""'
            }
          },
          {
            name: "globals",
            config:{
              id: "led_r",
              type: "float",
              initial_value: '1.0'
            }
          },
          {
            name: "globals",
            config:{
              id: "led_g",
              type: "float",
              initial_value: '1.0'
            }
          },
          {
            name: "globals",
            config:{
              id: "led_b",
              type: "float",
              initial_value: '1.0'
            }
          },
          {
            name: "globals",
            config:{
              id: "led_on_time",
              type: "int",
              initial_value: '200'
            }
          },
          {
            name: "globals",
            config:{
              id: "last_loadcell_value",
              type: "float",
              initial_value: '0.0'
            }
          },        
          {
            name: "script",
            config: {
              id: "handle_led_action",
              then: [
                {
                  lambda: 'ESP_LOGD("LED_CONTROL", "Executing action: %s", id(led_action).c_str());'
                },
                {
                  if: {
                    condition: {
                      lambda: 'return id(led_action) == "on";'
                    },
                    then: [
                      {
                        "light.turn_on": {
                          id: "leds",
                          brightness: 1.0,
                          red: '@!lambda return id(led_r);@',
                          green: '@!lambda return id(led_g);@',
                          blue: '@!lambda return id(led_b);@',
                          transition_length: "0s"
                        }
                      }
                    ]
                  }
                },
                {
                  if: {
                    condition: {
                      lambda: 'return id(led_action) == "off";'
                    },
                    then: [
                      {
                        "light.turn_off": {
                          id: "leds",
                          transition_length: "0s"
                        }
                      }
                    ]
                  }
                },
                {
                  if: {
                    condition: {
                      lambda: 'return id(led_action) == "blink";'
                    },
                    then: [
                      {
                        "light.turn_on": {
                          id: "leds",
                          brightness: 1.0,
                          red: '@!lambda return id(led_r);@',
                          green: '@!lambda return id(led_g);@',
                          blue: '@!lambda return id(led_b);@',
                          transition_length: "0s"
                        }
                      },
                      {
                        delay: '@!lambda return id(led_on_time);@'
                      },
                      {
                        "light.turn_off": {
                          id: "leds",
                          transition_length: "0s"
                        }
                      }
                    ]
                  }
                }
              ]
            }
          }
          

        ]
    
        componentObjects.forEach((element, j) => {
          deviceComponents = extractComponent(element, deviceComponents, [{ key: 'mqtt', nestedKey: 'on_message' }])
        })
    
        return deviceComponents
      }
      getSubsystem() {
        return {
          name: this.name,
          type: this.type,
          monitors: [
            {
              name: 'load',
              label: 'Load cell',
              description: 'Get load cell status',
              units: 'pts',
              endpoint: "/sensor/"+this.name+"/state",
              connectionType: 'mqtt',
            }
          ]
        }
      }
}

export function hx711(name, clkPin, gain, updateInterval, sensitivityBig, sensitivitySmall, smallThrottle, heartbeat) { 
  return new HX711(name, 'hx711', clkPin, gain, updateInterval, sensitivityBig, sensitivitySmall, smallThrottle, heartbeat);
}