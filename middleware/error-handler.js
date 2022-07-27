export function errorHandler(err, req, res, next) {
  let ret = {}
  if(err.status && err.status !== 500) {
    ret = {
      error: err.message,
      message: err.message,
      details: err.details,
    }
  } else {
    ret = Object.assign({}, err, {
      error: err.error || err.message,
      message: err.message || err.error,
      details: err.details,
    })
  }

  res.status(err.status || 500)
    .json(ret)
}