document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    const getCsrfToken = () => document.getElementById('csrf_token').value;
    
    // Helper function to update CSRF token if provided in response
    const updateCsrfToken = (data) => {
        if (data && data.csrf_token) {
            document.getElementById('csrf_token').value = data.csrf_token;
        }
    };
    
    document.getElementById('create-backup-btn').addEventListener('click', function() {
        this.disabled = true;
        this.textContent = 'Creating backup...';
        
        fetch('/api/backup/create', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            const message = document.getElementById('message');
            if (data.error) {
                message.textContent = data.error;
                message.className = 'message error';
            } else {
                message.textContent = data.message;
                message.className = 'message success';
                // Update CSRF token if provided
                updateCsrfToken(data);
                setTimeout(function() {
                    window.location.reload();
                }, 2000);
            }
            message.style.display = 'block';
            this.disabled = false;
            this.textContent = 'Create New Backup';
        })
        .catch(error => {
            console.error('Error:', error);
            this.disabled = false;
            this.textContent = 'Create New Backup';
        });
    });
    
    // Setup restore buttons
    document.querySelectorAll('.restore-btn').forEach(button => {
        button.addEventListener('click', function() {
            const file = this.getAttribute('data-file');
            if (confirm('Are you sure you want to restore from this backup? Current data will be replaced.')) {
                this.disabled = true;
                this.textContent = 'Restoring...';
                
                fetch('/api/backup/restore', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ file })
                })
                .then(response => response.json())
                .then(data => {
                    const message = document.getElementById('message');
                    if (data.error) {
                        message.textContent = data.error;
                        message.className = 'message error';
                    } else {
                        message.textContent = data.message;
                        message.className = 'message success';
                        // Update CSRF token if provided
                        updateCsrfToken(data);
                    }
                    message.style.display = 'block';
                    this.disabled = false;
                    this.textContent = 'Restore';
                })
                .catch(error => {
                    console.error('Error:', error);
                    this.disabled = false;
                    this.textContent = 'Restore';
                });
            }
        });
    });
    
    // Setup delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const file = this.getAttribute('data-file');
            if (confirm('Are you sure you want to delete this backup?')) {
                this.disabled = true;
                this.textContent = 'Deleting...';
                
                fetch('/api/backup/delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ file })
                })
                .then(response => response.json())
                .then(data => {
                    const message = document.getElementById('message');
                    if (data.error) {
                        message.textContent = data.error;
                        message.className = 'message error';
                    } else {
                        message.textContent = data.message;
                        message.className = 'message success';
                        // Update CSRF token if provided
                        updateCsrfToken(data);
                        // Remove the row from the table
                        this.closest('tr').remove();
                    }
                    message.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error:', error);
                    this.disabled = false;
                    this.textContent = 'Delete';
                });
            }
        });
    });
});