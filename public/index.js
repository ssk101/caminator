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

function makeControlGroup(controlType, controlName, value, description, cb) {
  console.log(description)
  const makeInput = (v) => {
    const input = Object.assign(document.createElement('input'), {
      name: controlName,
      placeholder: controlName,
      type: controlType,
      oninput: (e) => {
        debounce(() => cb(e))
      },
    })

    if(typeof v === 'boolean') {
      input.checked = v
      input.value = Number(v)
    } else if(typeof v === 'number') {
      input.value = parseFloat(v)
    }

    return input
  }
  const makeLabel = (v) => {
    return Object.assign(document.createElement('label'), {
      textContent: `${controlName}: ${v}`,
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

for(const [controlName, controlData] of Object.entries(await getMeta())) {
  const { controlType, value, description = [] } = controlData
  const controlGroup = makeControlGroup(
    controlType,
    controlName,
    value,
    description,
    setControls,
  )

  for(const attr of ['step', 'min', 'max']) {
    if(typeof controlData[attr] !== 'undefined') {
      controlGroup.querySelector('input')[attr] = controlData[attr]
    }
  }

  controls.insertAdjacentElement('afterbegin', controlGroup)
}

// const qualityControlGroup = makeControlGroup(
//   'number',
//   'quality',
//   20,
//   setQuality,
// )

// controls.insertAdjacentElement('afterbegin', qualityControlGroup)

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
    const { value, description = [] } = controlData

    for(const [i, v] of Object.entries([value].flat())) {
      const inputs = controls.querySelector(`.${controlName} .inputs[data-index="${i}"]`)
      inputs.dataset.values = value

      Object.assign(inputs.querySelector('label'), {
        textContent: `${controlName}: ${v}`,
        title: description.join(', '),
      })
      inputs.querySelector('input').value = v
    }
  }
}

async function setControls(e) {
  const inputs = e.target.parentElement
  const values = []

  for(const input of Array.from(inputs.querySelectorAll('input'))) {
    const v = input.type === 'checkbox' ? Boolean(input.value) : Number(input.value)
    values.push(v)
  }

  const actualValues = values.length === 1 ? values[0] : values

  inputs.dataset.values = actualValues

  const response = await fetch(`${main.dataset.root}/controls`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      [e.target.name]: actualValues,
    })
  }).then(res => res.json())

  await update(response)
}

// async function setQuality(e) {
//   const response = await fetch(`${main.dataset.root}/quality`, {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json',
//     },
//     body: e.target.value,
//   }).then(res => res.json())
// }
