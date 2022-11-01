const main = document.body.querySelector('main')
let waiting

const {
  root,
  quality,
  width,
  height,
} = main.dataset

async function get(endpoint, body = {}, method = 'get') {
  const data = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  }

  if(method.toLowerCase() === 'post') {
    data.body = JSON.stringify(body)
  }

  return fetch(`${main.dataset.root}/${endpoint}`, data)
    .then(res => res.json())
}

function updateStream() {
  const url = `url(${root}?${Date.now()})`
  let stream = main.querySelector('#stream')

  stream.style.backgroundImage = url
}

async function getControls() {
  return get('meta')
}

async function setControls(e) {
  const inputs = e.target.parentElement
  const values = []

  for(const input of Array.from(inputs.querySelectorAll('input'))) {
    const v = Number(input.value)
    values.push(v)
  }

  const actualValues = values.length === 1 ? values[0] : values

  inputs.dataset.values = actualValues

  const body = {
    [e.target.name]: actualValues,
  }

  const response = await get('controls', body, 'post')

  updateControls(response)
  updateStream()
}

async function getModes() {
  return get('modes')
}

async function setMode(e) {
  const body = {
    mode: e.target.id,
  }
  const controls = await get('mode', body, 'post')
  updateControls(controls)
  updateStream()
}

const debounce = (cb, delay = 1000) => {
  if(waiting) return

  waiting = true

  setTimeout(() => {
    cb()
    waiting = false
  }, delay)
}

function makeControlGroup(controlType, controlName, value, description = [], name, cb) {
  const makeInput = (v) => {
    const input = Object.assign(document.createElement('input'), {
      name: name || controlName,
      placeholder: controlName,
      type: controlType,
      oninput: (e) => {
        debounce(() => cb(e))
      },
    })

    input.value = parseFloat(v)
    return input
  }

  const makeLabel = (v) => {
    return Object.assign(document.createElement('label'), {
      textContent: `${controlName}${controlType !== 'radio' ? ': ' + v : ''}`,
      title: description.join(', '),
    })
  }

  const controlGroup = Object.assign(document.createElement('div'), {
    className: `control ${controlName}`,
  })

  for(const [i, v] of Object.entries([value].flat())) {
    const inputs = Object.assign(document.createElement('div'), {
      className: 'inputs',
    })

    Object.assign(inputs.dataset, {
      index: i,
      values: value,
    })

    inputs.append(makeLabel(v), makeInput(v))
    controlGroup.append(inputs)
  }

  return controlGroup
}

async function updateControls(meta) {
  for(const [controlName, controlData] of Object.entries(meta)) {
    const { value, description = [] } = controlData

    for(const [i, v] of Object.entries([value].flat())) {
      const inputs = controls.querySelector(`.${controlName} .inputs[data-index="${i}"]`)
      inputs.dataset.values = value

      Object.assign(inputs.querySelector('label'), {
        textContent: `${controlName}: ${v}`,
        title: description.join(', '),
      })

      const input = inputs.querySelector('input')
      input.value = v

      if(['checkbox', 'radio'].includes(input.type)) {
        input.setAttribute('checked', !!v)
      }
    }
  }
}

const controls = Object.assign(document.createElement('div'), {
  id: 'controls',
})

main.append(controls)

updateStream()

const cameraControls = await getControls()
const modes = await getModes()

for(const mode of Object.keys(modes)) {
  const controlGroup = makeControlGroup(
    'radio',
    mode,
    modes[mode].value,
    [],
    'modes',
    setMode,
  )
  controlGroup.querySelector('input').id = mode
  controls.insertAdjacentElement('afterbegin', controlGroup)
}

for(const [controlName, controlData] of Object.entries(cameraControls)) {
  const { controlType, value, description = [] } = controlData
  const controlGroup = makeControlGroup(
    controlType,
    controlName,
    value,
    description,
    controlName,
    setControls,
  )

  for(const attr of ['step', 'min', 'max']) {
    if(typeof controlData[attr] !== 'undefined') {
      controlGroup.querySelector('input')[attr] = controlData[attr]
    }
  }

  controls.insertAdjacentElement('afterbegin', controlGroup)
}


