function viewConversation(conversationId) {
    window.location.href = `/interact?conversation_id=${conversationId}`;
}

function deleteConversation(conversationId) {
    if (confirm('Are you sure you want to delete this conversation?')) {
        fetch(`/delete_conversation/${conversationId}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the conversation card from the DOM
                const card = document.querySelector(`[data-id="${conversationId}"]`);
                card.remove();
            } else {
                alert('Failed to delete conversation');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the conversation');
        });
    }
}