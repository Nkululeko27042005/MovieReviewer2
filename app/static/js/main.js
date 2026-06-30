// ===== DOM Ready =====
document.addEventListener('DOMContentLoaded', function() {
    // Flash messages auto-dismiss
    initFlashMessages();
    
    // Mobile menu toggle
    initMobileMenu();
    
    // Notification badge update
    updateNotificationBadge();
    
    // Infinite scroll for feed
    initInfiniteScroll();
});

// ===== Flash Messages =====
function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        const closeBtn = msg.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                msg.style.animation = 'slideInRight 0.3s reverse';
                setTimeout(() => msg.remove(), 300);
            });
        }
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (msg.parentNode) {
                msg.style.animation = 'slideInRight 0.3s reverse';
                setTimeout(() => msg.remove(), 300);
            }
        }, 5000);
    });
}

// ===== Mobile Menu =====
function initMobileMenu() {
    const btn = document.getElementById('mobileMenuBtn');
    const menu = document.getElementById('mobileMenu');
    
    if (btn && menu) {
        btn.addEventListener('click', () => {
            menu.classList.toggle('open');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!btn.contains(e.target) && !menu.contains(e.target)) {
                menu.classList.remove('open');
            }
        });
    }
}

// ===== Notification Badge =====
async function updateNotificationBadge() {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;
    
    try {
        const response = await axios.get('/api/users/notifications?status=unread&limit=1');
        const data = response.data;
        
        if (data.unread_count > 0) {
            badge.style.display = 'block';
            badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        console.error('Failed to fetch notification count:', error);
    }
}

// ===== Infinite Scroll =====
function initInfiniteScroll() {
    let loading = false;
    let page = 1;
    const container = document.querySelector('.infinite-scroll-container');
    
    if (!container) return;
    
    const observer = new IntersectionObserver(async (entries) => {
        if (entries[0].isIntersecting && !loading) {
            const loadMore = container.dataset.loadMore;
            if (!loadMore) return;
            
            loading = true;
            page++;
            
            try {
                const response = await fetch(`${loadMore}?page=${page}`);
                const data = await response.json();
                
                if (data.reviews && data.reviews.length > 0) {
                    // Append new reviews
                    const reviewsHtml = data.reviews.map(review => renderReviewCard(review)).join('');
                    container.insertAdjacentHTML('beforeend', reviewsHtml);
                } else {
                    // No more reviews, remove observer
                    observer.disconnect();
                    document.querySelector('.load-more-end')?.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Failed to load more reviews:', error);
            } finally {
                loading = false;
            }
        }
    }, { threshold: 0.1 });
    
    observer.observe(container.querySelector('.load-more-trigger') || container);
}

// ===== Review Card Renderer =====
function renderReviewCard(review) {
    return `
        <div class="review-card" data-review-id="${review.id}">
            <div class="review-card-header">
                <div class="review-author">
                    <img src="${review.author_profile_picture || '/static/images/default-avatar.png'}" alt="${review.author_username}">
                    <div class="review-author-info">
                        <a href="/users/${review.author_id}" class="review-author-name">${review.author_username}</a>
                        <span class="review-date">${new Date(review.published_at).toLocaleDateString()}</span>
                    </div>
                </div>
                <div class="review-rating-badge stars-display">
                    ${Array.from({length: 10}, (_, i) => i + 1 <= Math.floor(review.overall_rating) ? '<i class="fas fa-star" style="color: var(--warning-color);"></i>' : '<i class="far fa-star" style="color: var(--warning-color);"></i>').join('')}
                    <span style="margin-left: 8px; font-size: 0.9em;">(${review.overall_rating.toFixed(1)})</span>
                </div>
            </div>
            <div class="review-body">
                <h3 class="review-title">${review.title}</h3>
                <div class="review-movie"><i class="fas fa-film"></i> ${review.movie_name}</div>
                ${review.genres && review.genres.length > 0 ? `<div class="review-genres">${review.genres.map(g => `<span class="genre-tag">${g}</span>`).join('')}</div>` : ''}
                
                ${(review.review_poster_url || review.movie_poster_url) ? `
                <div class="poster-stack">
                    ${review.review_poster_url ? `
                    <div class="poster-item">
                        <img src="${review.review_poster_url}" alt="Review Poster">
                        <div class="poster-label">Review Poster</div>
                    </div>` : ''}
                    ${review.movie_poster_url ? `
                    <div class="poster-item">
                        <img src="${review.movie_poster_url}" alt="Movie Poster">
                        <div class="poster-label">Movie Poster</div>
                    </div>` : ''}
                </div>` : ''}

                <p class="review-summary">${review.overall_thoughts}</p>
                ${review.has_spoilers ? '<span class="review-spoiler"><i class="fas fa-exclamation-triangle"></i> Contains Spoilers</span>' : ''}
            </div>
            <div class="review-footer">
                <div class="review-actions">
                    <button class="review-action-btn like-btn" onclick="toggleLike(${review.id})">
                        <i class="fas fa-heart ${review.is_liked ? 'liked' : ''}"></i>
                        <span class="like-count">${review.likes_count}</span>
                    </button>
                    <button class="review-action-btn" onclick="toggleSave(${review.id})">
                        <i class="fas fa-bookmark ${review.is_saved ? 'saved' : ''}"></i>
                        <span class="save-count">${review.saves_count}</span>
                    </button>
                    <button class="review-action-btn" onclick="scrollToComments(${review.id})">
                        <i class="fas fa-comment"></i>
                        <span class="comment-count">${review.comments_count}</span>
                    </button>
                </div>
                <a href="/reviews/${review.id}" class="btn btn-outline btn-sm">Read More</a>
            </div>
        </div>
    `;
}

// ===== Like/Unlike Review =====
async function toggleLike(reviewId) {
    try {
        const reviewCard = document.querySelector(`.review-card[data-review-id="${reviewId}"]`);
        const likeBtn = reviewCard.querySelector('.like-btn');
        const isLiked = likeBtn.querySelector('i').classList.contains('liked');
        
        const response = await axios({
            method: isLiked ? 'DELETE' : 'POST',
            url: `/api/reviews/${reviewId}/like`
        });
        
        if (response.data.success) {
            const icon = likeBtn.querySelector('i');
            const countSpan = likeBtn.querySelector('.like-count');
            let count = parseInt(countSpan.textContent);
            
            if (isLiked) {
                icon.classList.remove('liked');
                count--;
            } else {
                icon.classList.add('liked');
                count++;
            }
            countSpan.textContent = count;
        }
    } catch (error) {
        console.error('Failed to toggle like:', error);
        showFlashMessage('error', 'Failed to like/unlike review');
    }
}

// ===== Save/Unsave Review =====
async function toggleSave(reviewId) {
    try {
        const reviewCard = document.querySelector(`.review-card[data-review-id="${reviewId}"]`);
        const saveBtn = reviewCard.querySelector('.review-action-btn:nth-child(2)');
        const isSaved = saveBtn.querySelector('i').classList.contains('saved');
        
        const response = await axios({
            method: isSaved ? 'DELETE' : 'POST',
            url: `/api/reviews/${reviewId}/save`
        });
        
        if (response.data.success) {
            const icon = saveBtn.querySelector('i');
            if (isSaved) {
                icon.classList.remove('saved');
            } else {
                icon.classList.add('saved');
            }
        }
    } catch (error) {
        console.error('Failed to toggle save:', error);
        showFlashMessage('error', 'Failed to save/unsave review');
    }
}

// ===== Comments Scroll =====
function scrollToComments(reviewId) {
    const element = document.getElementById(`comments-${reviewId}`);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ===== Flash Message Helper =====
function showFlashMessage(type, message) {
    const container = document.querySelector('.flash-messages');
    if (!container) return;
    
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    const flash = document.createElement('div');
    flash.className = `flash-message flash-${type}`;
    flash.innerHTML = `
        <i class="fas fa-${icons[type] || 'info-circle'}"></i>
        ${message}
        <button class="flash-close">&times;</button>
    `;
    
    container.appendChild(flash);
    
    // Auto dismiss
    setTimeout(() => {
        flash.style.animation = 'slideInRight 0.3s reverse';
        setTimeout(() => flash.remove(), 300);
    }, 5000);
    
    // Close button
    flash.querySelector('.flash-close').addEventListener('click', () => {
        flash.style.animation = 'slideInRight 0.3s reverse';
        setTimeout(() => flash.remove(), 300);
    });
}

// ===== Form Validation =====
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        const errorEl = input.parentElement.querySelector('.error-text');
        if (!input.value.trim()) {
            input.classList.add('error');
            if (errorEl) errorEl.textContent = 'This field is required';
            isValid = false;
        } else {
            input.classList.remove('error');
            if (errorEl) errorEl.textContent = '';
        }
    });
    
    return isValid;
}

// ===== File Upload Preview =====
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    } else {
        preview.style.display = 'none';
    }
}

// ===== Rating Stars =====
function initRatingStars() {
    const starContainers = document.querySelectorAll('.rating-stars');
    
    starContainers.forEach(container => {
        const stars = container.querySelectorAll('.star');
        const input = container.querySelector('input[type="hidden"]');
        const valueDisplay = container.querySelector('.rating-value');
        
        stars.forEach(star => {
            star.addEventListener('mouseenter', function() {
                const value = parseInt(this.dataset.value);
                highlightStars(stars, value);
            });
            
            star.addEventListener('click', function() {
                const value = parseInt(this.dataset.value);
                if (input) input.value = value;
                if (valueDisplay) valueDisplay.textContent = value.toFixed(1);
                highlightStars(stars, value);
            });
        });
        
        container.addEventListener('mouseleave', function() {
            const currentValue = input ? parseFloat(input.value) : 0;
            highlightStars(stars, currentValue);
        });
    });
}

function highlightStars(stars, value) {
    stars.forEach(star => {
        const starValue = parseInt(star.dataset.value);
        if (starValue <= value) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

// ===== Modal =====
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal on overlay click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
            closeModal(modal.id);
        });
    }
});

// ===== Export functions to global scope =====
window.toggleLike = toggleLike;
window.toggleSave = toggleSave;
window.scrollToComments = scrollToComments;
window.showFlashMessage = showFlashMessage;
window.validateForm = validateForm;
window.previewImage = previewImage;
window.openModal = openModal;
window.closeModal = closeModal;
window.initRatingStars = initRatingStars;