const name = document.getElementById("username")
const password = document.getElementById("password")
const confirmation = document.getElementById("confirmation")
const form = document.getElementById("form")
const errorElement = document.getElementById('error')

form.addEventListener('submit', (e) =>{
    let messages =[]
    if (name.value === '' || name.value === null) {
        messages.push('Discord login is required')
    }

    if (password.value === '' || password.value === null) {
        messages.push('Password is required')
    }

    if (confirmation.value === '' || confirmation.value === null) {
        messages.push('Password confirmation is required')
    }

    if (password.value != confirmation.value) {
        messages.push('Password and confirmation are different')
    }

    if (messages.length > 0){
        e.preventDefault()
        errorElement.innerText = messages.join('\r\n')
    }
    
})
