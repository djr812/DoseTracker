
// Wait for the DOM to fully load before running the script
document.addEventListener('DOMContentLoaded', function () {

    // Get the table body element where we will add the rows
    const medicinesTableBody = document.getElementById('medicines-tbody');

    // Check if the 'medicines' data exists and is an array
    if (Array.isArray(window.medicines)) {
        // Loop through each medicine and create a table row
        window.medicines.forEach(medicine => {
            // Create a new table row
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${medicine.name}</td>
                <td>${medicine.dosage}</td>
                <td>${medicine.frequency}</td>
                <td>${medicine.notes || 'N/A'}</td>
                <td>
                    <button class="btn btn-primary" onclick="window.location.href='/medicines/edit_medicine/${medicine.id}'">Edit</button>
                    <button class="btn btn-danger" onclick="deleteMedicine(${medicine.id})">Delete</button>
                </td>
            `;

            // Append the row to the table body
            medicinesTableBody.appendChild(row);
        });
    } else {
        console.error("Medicines data is not in the expected format or is missing");
    }

    // Function to handle deleting a medicine
    function deleteMedicine(medicineId) {
        if (confirm("Are you sure you want to delete this medicine?")) {
            fetch(`/delete_medicine/${medicineId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            }).then(response => {
                if (response.ok) {
                    location.reload();  // Reload the page to reflect the changes
                } else {
                    alert('Failed to delete medicine');
                }
            });
        }
    }
});
