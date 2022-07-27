export function serialize(opts, handler) {
  return async function(req, res, next) {
    try {
      const response = await handler(req, res, next)

      if(Buffer.isBuffer(response)) {
        res.set('Content-Encoding', 'gzip')
        res.set('Content-Type', 'application/json')
        res.send(response)
      } else {
        res.json(response)
      }
    } catch (err) {
      next(err)
    }
  }
}