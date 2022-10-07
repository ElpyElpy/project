// Check for errors
const name = document.getElementById("username")
const password = document.getElementById("password")
const confirmation = document.getElementById("confirmation")
const form = document.getElementById("form")
const errorElement = document.getElementById('error')
const tokensToAdd = document.getElementById('tokens_to_add')
const form_2 = document.getElementById("form_2")


form_2.addEventListener('submit', (e) => {
    let messages = []
    let tta = tokensToAdd.value * 1;

    var countDecimals = function (value) {
        if(Math.floor(value) === value) return 0;
        return value.toString().split(".")[1].length || 0; 
        }

    if (tta <= 0) {
        console.log("ERROR")
        console.log(isNaN(tta))
        messages.push('Number of tokens should be positive')
    }

    
    if (tokensToAdd.value === '' || tokensToAdd.value == null) {
        console.log(tta)
        console.log("error")
        messages.push('Number of tokens is required')
    }

    if (isNaN(tta)){
        console.log(tta)
        console.log("error")
        messages.push('Should be a positive number')
    }

    if (countDecimals(tta) > 5){
        console.log("error")
        messages.push('Maximum 5 decimals')
    }

    if (messages.length > 0) {
        e.preventDefault()
        errorElement.innerText = messages[0]
    }
})




// Modal view for buying tokens
const open = document.getElementById('open');
const close = document.getElementById('close');
const modal_container = document.getElementById('modal_container');


open.addEventListener('click', () => {
    modal_container.classList.add("show");

});

close.addEventListener('click', () => {
    modal_container.classList.remove("show");

});



