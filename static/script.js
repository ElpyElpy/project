// Check for errors
const name = document.getElementById("username")
const password = document.getElementById("password")
const confirmation = document.getElementById("confirmation")
const form = document.getElementById("form")
const errorElement = document.getElementById('error')
const tokensToAdd = document.getElementById('tokens_to_add')
const form_2 = document.getElementById("form_2")
const symbol = document.getElementById("token")


form_2.addEventListener('submit', (e) => {
    let messages = []
    let tta = tokensToAdd.value * 1;

    var countDecimals = function (value) {
        if(Math.floor(value) === value) return 0;
        return value.toString().split(".")[1].length || 0; 
        }


    if (tta <= 0) {
        messages.push('Number of tokens should be positive')
    }

    
    if (tokensToAdd.value === '' || tokensToAdd.value == null) {
        messages.push('Number of tokens is required')
    }

    if (isNaN(tta)){
        e.preventDefault()
        messages.push('Number of tokens should be positive')
        errorElement.innerText = messages[0]
    }

    if (countDecimals(tta) > 5){
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


var countDecimals = function(value) {
    if (Math.floor(value) !== value)
        return value.toString().split(".")[1].length || 0;
    return 0;
}