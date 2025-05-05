const execSync = require('child_process').execSync;

const DEV_SERVER_URL = "http://127.0.0.1:8000"
const args = process.argv.slice(2);
const timeout = args[0] ?? 300000;// default 5 min
const RETRY_TIME = 1000 // 1 sec

const healthCheck = () => { // Check system is up and ready to use
    console.log('Running healthcheck, waiting to be ready...')
    return new Promise((resolve, reject) => {
        const isReady = () => {
            console.log('Checking if system is ready...')
            let isEnabled = execSync(`curl --max-time 10 -s ${DEV_SERVER_URL} | grep -q "__next" && echo true || echo false`, { encoding: 'utf-8' }).trim()
            console.log('isEnabled?', isEnabled)
            if (isEnabled === 'true') {
                console.log('System Ready!')
                clearInterval(interval)
                resolve()
            }
            else {
                console.log('healthchecking, please wait...')
            }
        }
        let interval = setInterval(isReady, RETRY_TIME);
        setTimeout(() => {
            clearInterval(interval)
            reject("Error: healthcheck timeout.")
        }, timeout)
    })
}

const main = async () => {
    await healthCheck()
      .catch((msg) => {
        console.error(msg)
      })
    process.exit()
}
main()
