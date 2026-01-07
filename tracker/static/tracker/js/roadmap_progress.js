/**
 * Roadmap Progress Tracker
 * Handles checkbox interactions and progress updates via AJAX
 */

(function() {
    'use strict';

    // Get CSRF token from cookie
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

    const csrftoken = getCookie('csrftoken');

    // Toggle checklist item completion
    function toggleChecklistItem(itemId, checkboxElement) {
        // Disable checkbox during request
        checkboxElement.disabled = true;

        // Send AJAX request
        fetch(`/roadmap-items/${itemId}/toggle/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update checkbox state
                updateCheckboxState(checkboxElement, data.is_completed);
                
                // Update completion timestamp
                updateCompletionTimestamp(checkboxElement, data.completed_at);
                
                // Update progress bars and percentages
                updateProgress(data);
                
                // Show success feedback
                showSuccessFeedback(checkboxElement);
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('Error toggling item:', error);
            alert('Failed to update task. Please try again.');
            
            // Revert checkbox state
            checkboxElement.checked = !checkboxElement.checked;
        })
        .finally(() => {
            // Re-enable checkbox
            checkboxElement.disabled = false;
        });
    }

    // Update checkbox visual state
    function updateCheckboxState(checkbox, isCompleted) {
        const checkboxDiv = checkbox.closest('.checklist-item').querySelector('.checkbox');
        const checklistText = checkbox.closest('.checklist-item').querySelector('.checklist-text');
        const checklistItem = checkbox.closest('.checklist-item');
        
        if (isCompleted) {
            checkboxDiv.classList.add('checked');
            checklistItem.classList.add('completed');
            
            // Add strikethrough animation
            checklistText.style.transition = 'all 0.3s ease';
        } else {
            checkboxDiv.classList.remove('checked');
            checklistItem.classList.remove('completed');
        }
    }

    // Update completion timestamp
    function updateCompletionTimestamp(checkbox, completedAt) {
        const checklistItem = checkbox.closest('.checklist-item');
        let timestampDiv = checklistItem.querySelector('.completion-timestamp');
        
        if (completedAt) {
            // Create or update timestamp
            if (!timestampDiv) {
                timestampDiv = document.createElement('div');
                timestampDiv.className = 'completion-timestamp';
                checklistItem.appendChild(timestampDiv);
            }
            
            const date = new Date(completedAt);
            const formattedDate = date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
            timestampDiv.innerHTML = `✓ Completed ${formattedDate}`;
            timestampDiv.style.fontSize = '0.875rem';
            timestampDiv.style.color = '#10B981';
            timestampDiv.style.marginTop = '0.25rem';
        } else {
            // Remove timestamp if unchecked
            if (timestampDiv) {
                timestampDiv.remove();
            }
        }
    }

    // Update progress bars and percentages
    function updateProgress(data) {
        // Update step progress (if on roadmap detail page)
        const stepProgressBar = document.querySelector('.step-progress-bar');
        const stepProgressText = document.querySelector('.step-progress-text');
        
        if (stepProgressBar && data.step_progress !== undefined) {
            animateProgressBar(stepProgressBar, data.step_progress);
            
            if (stepProgressText) {
                stepProgressText.textContent = `${data.step_completed} / ${data.step_total} complete`;
            }
        }
        
        // Update roadmap overall progress
        const roadmapProgressBar = document.querySelector('.roadmap-progress-fill');
        const roadmapProgressPercentage = document.querySelector('.roadmap-progress-percentage');
        const roadmapProgressDetails = document.querySelector('.roadmap-progress-details');
        
        if (roadmapProgressBar && data.roadmap_progress !== undefined) {
            animateProgressBar(roadmapProgressBar, data.roadmap_progress);
            
            if (roadmapProgressPercentage) {
                roadmapProgressPercentage.textContent = `${Math.round(data.roadmap_progress)}%`;
            }
            
            if (roadmapProgressDetails) {
                roadmapProgressDetails.textContent = `${data.roadmap_completed} / ${data.roadmap_total} items completed`;
            }
        }
    }

    // Animate progress bar
    function animateProgressBar(progressBar, newPercentage) {
        progressBar.style.transition = 'width 0.5s ease';
        progressBar.style.width = `${newPercentage}%`;
        
        // Update text inside progress bar if it exists
        const progressText = progressBar.querySelector('.progress-text');
        if (progressText && newPercentage > 10) {
            progressText.textContent = `${Math.round(newPercentage)}%`;
        }
    }

    // Show success feedback
    function showSuccessFeedback(checkbox) {
        const checklistItem = checkbox.closest('.checklist-item');
        
        // Add success flash animation
        checklistItem.style.transition = 'background-color 0.3s ease';
        const originalBg = checklistItem.style.backgroundColor;
        checklistItem.style.backgroundColor = '#D1FAE5';
        
        setTimeout(() => {
            checklistItem.style.backgroundColor = originalBg;
        }, 300);
    }

    // Initialize checkbox listeners
    function initializeCheckboxes() {
        // Find all checklist items with checkboxes
        const checkboxes = document.querySelectorAll('.checklist-item input[type="checkbox"]');
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function(e) {
                const itemId = this.getAttribute('data-item-id');
                
                if (!itemId) {
                    console.error('No item ID found on checkbox');
                    return;
                }
                
                toggleChecklistItem(itemId, this);
            });
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeCheckboxes);
    } else {
        initializeCheckboxes();
    }

})();