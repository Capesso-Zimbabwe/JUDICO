// Client Management Dashboard JavaScript

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTables for client tables
    if (document.getElementById('clientsTable')) {
        $('#clientsTable').DataTable({
            responsive: true,
            order: [[0, 'asc']],
            pageLength: 10,
            lengthMenu: [[5, 10, 25, 50, -1], [5, 10, 25, 50, "All"]]
        });
    }
    
    // Handle document deletion via AJAX
    const deleteDocumentButtons = document.querySelectorAll('.delete-document');
    if (deleteDocumentButtons) {
        deleteDocumentButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const documentId = this.getAttribute('data-document-id');
                
                if (confirm('Are you sure you want to delete this document?')) {
                    // Send AJAX request to delete document
                    fetch(`/client/documents/${documentId}/delete/`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Remove the row from the table
                            this.closest('tr').remove();
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
                }
            });
        });
    }
    
    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});