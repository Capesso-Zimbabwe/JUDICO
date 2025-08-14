document.addEventListener('DOMContentLoaded', function() {
    // Get the modal element
    const transactionFormModalElement = document.getElementById('transaction-form-modal');
    
    // Check if the modal element exists on the page
    if (transactionFormModalElement) {
        // Initialize the modal with the global modalOptions
        window.transactionFormModal = new Modal(transactionFormModalElement, modalOptions);
        
        // Add event listener for the fillThisForm function
        window.fillThisForm = function(data) {
            // This function can be used to pre-fill the form with data
            console.log('fillThisForm called with data:', data);
            // Implementation for pre-filling form fields would go here
        };
        
        console.log('Transaction form modal initialized successfully');
    } else {
        console.log('Transaction form modal element not found on this page');
    }
});