// This file contains JavaScript code for client-side functionality.

document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript is loaded and ready to go!');

    // Example of a simple interaction
    const button = document.getElementById('myButton');
    if (button) {
        button.addEventListener('click', function() {
            alert('Button was clicked!');
        });
    }
});