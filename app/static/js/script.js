
document.querySelector('form').addEventListener('submit', function (event) {
    // Prevent form submission if there are any issues (like empty fields)
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!email || !password) {
        event.preventDefault();
        alert("Both fields are required.");
    }
});
