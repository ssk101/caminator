import fs from 'node:fs'
import path from 'node:path'
import express from 'express'
import { serialize } from '../middleware/serialize.js'
import { errorHandler } from '../middleware/error-handler.js'

const __dirname = ((await import('path')).dirname)(((await import('url')).fileURLToPath)(import.meta.url))

export async function router(settings) {
  const {
    routes = {},
    middlewares = [],
    dataset = {},
    title = 'Untitled',
    src = 'index.js',
    routesBase = '',
    injected = []
  } = settings

  const re = new RegExp(/(\$)(\w+)/, 'g')
  const html = fs.readFileSync(path.join(__dirname, '..', 'public', 'index.html'), { encoding: 'utf8' })
    .split('\n')
    .map(line => {
      if(line.match(re)) {
        line = line.replace(re, (_, m1, m2) => {
          return injected[m2]
        })
      }
      return line
    })
    .join('\n')

  const router = express.Router()

  router.use(errorHandler)

  for(const middleware of middlewares) {
    router.use(middleware)
  }

  router.get('/', (req, res, next) => {
    res.setHeader("Content-Type", "text/html")
    res.send(html)
  })

  router.get('/stream', (req, res, next) => {
    res.redirect(injected.CAMINATOR_STREAM_URL)
    next()
  })

  return router
}