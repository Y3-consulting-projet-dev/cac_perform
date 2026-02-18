import { Notyf } from "notyf"

export function useNotyf() {
    const notyf = new Notyf({
        types: [
            {
                type: 'info',
                background: 'blue',
                duration: 3000
            }
        ]
    })

    function triggerNotyf(message, state, options={}) {
        const {
            duration = 2000,
            position = {
                x: 'right',
                y: 'top'
            }
        } = options

        if (state === 'success') {
            notyf.open({
                type: 'success',
                message: message,
                duration: duration,
                position: {...position}
            })
        } else if (state === 'info') {
            notyf.open({
                type: 'info',
                message: message
            })
        } else if (state === 'error') {
            notyf.open({
                type: 'error',
                message: message,
                duration: duration,
                position: {...position}
            })
        }
    }

    return {
        trigger: triggerNotyf
    }
}