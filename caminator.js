import os from 'node:os'
import path from 'node:path'
import http from 'node:http'
import fs from 'node:fs'
import readline from 'node:readline'
import { execSync, spawn } from 'node:child_process'
import express from 'express'
import compression from 'compression'
import terminator from 'http-terminator'
import { router } from './lib/router.js'
import { serialize } from './middleware/serialize.js'
import { errorHandler } from './middleware/error-handler.js'

const { createHttpTerminator } = terminator

const __dirname = ((await import('path')).dirname)(((await import('url')).fileURLToPath)(import.meta.url))

function getLocalIP() {
  let localIP = '127.0.0.1'
  const interfaces = os.networkInterfaces()

  for(const iface in interfaces) {
    for(const details of interfaces[iface]) {
      const { family, internal, address } = details

      if(family !== 'IPv4' || !address || internal) continue

      const ip = address.match(/((192|10)\.(?!0)\d+\.(\d+)\.(?!0)\d+)/)

      if(ip) return ip[0]
    }
  }

  return localIP
}

const CAMINATOR_ROOT = `http://${getLocalIP()}:${process.env.CAMINATOR_PORT || 8888}`

const {
  CAMINATOR_VIDEO_WIDTH = 2592,
  CAMINATOR_VIDEO_HEIGHT = 1944,
  CAMINATOR_TITLE = 'Caminator',
  CAMINATOR_STREAM_URL = `${CAMINATOR_ROOT}/stream`
} = process.env

export async function createServer(config = {}) {
  const { app } = await createApp(config)

  config.app ??= app

  const settings = Object.assign({}, {
    port: 3000,
    onExit: function(e) {
      killScript()
    },
  }, config)


  const server = http.createServer(settings.app)

  const graceful = createHttpTerminator({
    gracefulTerminationTimeout: 1 * 1000,
    server,
  })

  server.listen(settings.port)
  console.info('Listening on', settings.port)

  process.on('SIGUSR2', () => {
    require('v8').writeHeapSnapshot()
  })

  process.on('SIGABRT', () => {
    settings.onExit()

    server.close(() => {
      process.exit()
    })
  })

  process.on('SIGTERM', () => {
    settings.onExit()

    server.close(() => {
      process.exit()
    })
  })

  process.on('SIGINT', () => {
    settings.onExit()

    server.close(() => {
      process.exit()
    })
  })

  process.on('exit', () => {
    settings.onExit()
    server.close()
  })

  if (process.platform === 'win32') {
    var rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    })

    rl.on('SIGINT', () => {
      process.emit('SIGINT')
    })
  }

  return server
}

export async function createApp(config = {}) {
  const defaults = {
    publicDir: 'public',
    favicon: 'favicon.png',
    json: {
      limit: '50MB',
      strict: true,
      inflate: true,
      type: ['application/json'],
    },
    cors: Object.assign({
      methods: ['GET', 'POST', 'PATCH', 'PUT'],
      allowedHeaders: [
        'Content-Type',
      ],
    }, config.cors || {}),
    middlewares: [],
    injected: {
      CAMINATOR_VIDEO_WIDTH,
      CAMINATOR_VIDEO_HEIGHT,
      CAMINATOR_TITLE,
      CAMINATOR_STREAM_URL,
      CAMINATOR_ROOT,
    },
  }

  const settings = Object.assign({}, defaults, config)

  const app = express()
  app.enable('trust proxy')
  app.disable('x-powered-by')
  app.set('startTime', new Date())
  app.use(compression())
  app.use(express.json(settings.json))

  if(settings.cors) {
    const { default: cors } = await import('cors')
    app.use(cors(settings.cors))
  }

  app.use(await router(settings))

  for(const middleware of settings.middlewares) {
    if(typeof middleware !== 'function') {
      console.warn('Middleware is not a function, got', middleware)
      continue
    }

    app.use(middleware)
  }

  app.use(express.static(path.join(__dirname, settings.publicDir)))

  return { app }
}

async function hastaLaVista(baby) {
  await killScript()

  baby
    .terminate()
    .catch(err => console.error(err))
}

async function killScript() {
  return new Promise(resolve => {
    try {
      execSync([
        'pkill',
        '-f',
        "'(stream\.py)'",
      ].join(' '))
    } catch (e) {
      console.log('no scripts to kill')
    }

    resolve()
  })
}


const script = spawn(
  'python3',
  [
    path.join(__dirname, 'stream.py'),
  ]
)

script.stdout.on('data', async (data) => {
  const msg = data.toString().trim()
  console.log(data.toString().trim())
})

script.stderr.on('data', async (data) => {
  const msg = data.toString().trim()
  console.error(data.toString().trim())
})

script.on('close', (code) => {
  console.error({ code })
})


createServer()