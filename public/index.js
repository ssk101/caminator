const main = document.body.querySelector('main')
const controls = main.querySelector('#controls')

async function getMeta() {
  return await fetch(`${main.dataset.root}/meta`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  }).then(res => res.json())
}

let waiting

function makeControlGroup(controlType, controlName, value, cb) {
  const controlGroup = Object.assign(document.createElement('div'), {
    className: `control ${controlName}`,
  })

  const label = Object.assign(document.createElement('label'), {
    textContent: `${controlName}: ${value}`,
    for: controlName,
  })

  const input = Object.assign(document.createElement('input'), {
    id: controlName,
    placeholder: controlName,
    type: controlType,
    value,
    oninput: (e) => {
      debounce(() => cb(e))
    },
  })

  controlGroup.append(label, input)
  return controlGroup
}

for(const [controlName, controlData] of Object.entries(await getMeta())) {
  const { control, value } = controlData
  const controlGroup = makeControlGroup(
    control,
    controlName,
    value,
    setControls,
  )

  for(const attr of ['step', 'min', 'max']) {
    if(typeof controlData[attr] !== 'undefined') {
      controlGroup.querySelector('input')[attr] = controlData[attr]
    }
  }

  controls.insertAdjacentElement('afterbegin', controlGroup)
}

const qualityControlGroup = makeControlGroup(
  'number',
  'quality',
  20,
  setQuality,
)

controls.insertAdjacentElement('afterbegin', qualityControlGroup)

const debounce = (cb, delay = 1000) => {
  if(waiting) return

  waiting = true

  setTimeout(() => {
    cb()
    waiting = false
  }, delay)
}

async function update(meta) {
  for(const [controlName, controlData] of Object.entries(meta)) {
    const value = controlData.value
    controls.querySelector(`.${controlName} label`).textContent = `${controlName}: ${value}`
    controls.querySelector(`.${controlName} input`).value = value
  }
}

function getControls() {
  return Array.from(controls.querySelectorAll('input')).reduce((acc, input) => {
    acc[input.id] = input.value
    return acc
  }, {})
}

async function setControls(e) {
  const response = await fetch(`${main.dataset.root}/controls`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      [e.target.id]: Number(e.target.value),
    })
  }).then(res => res.json())

  await update(response)
}

async function setQuality(e) {
  const response = await fetch(`${main.dataset.root}/quality`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: e.target.value,
  }).then(res => res.json())
}
