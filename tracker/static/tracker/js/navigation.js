// Navigation Menu JavaScript
// Handles mobile hamburger menu and navigation interactions

document.addEventListener('DOMContentLoaded', function() {
    console.log('Navigation script loaded');
    
    // Get elements
    const hamburger = document.querySelector('.hamburger');
    const mobileMenu = document.querySelector('.mobile-menu');
    const menuBackdrop = document.querySelector('.menu-backdrop');
    const mobileMenuItems = document.querySelectorAll('.mobile-menu-item');
    
    // Check if elements exist
    if (!hamburger || !mobileMenu || !menuBackdrop) {
        console.log('Navigation elements not found');
        return;
    }
    
    console.log('Navigation elements found');
    
    // Toggle menu function
    function toggleMenu() {
        hamburger.classList.toggle('active');
        mobileMenu.classList.toggle('active');
        menuBackdrop.classList.toggle('active');
        
        // Prevent body scroll when menu is open
        if (mobileMenu.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }
    
    // Close menu function
    function closeMenu() {
        hamburger.classList.remove('active');
        mobileMenu.classList.remove('active');
        menuBackdrop.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    // Hamburger click
    hamburger.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleMenu();
    });
    
    // Backdrop click
    menuBackdrop.addEventListener('click', closeMenu);
    
    // Menu item click
    mobileMenuItems.forEach(item => {
        item.addEventListener('click', closeMenu);
    });
    
    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
            closeMenu();
        }
    });
    
    // Close menu on window resize to desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992 && mobileMenu.classList.contains('active')) {
            closeMenu();
        }
    });
    
    console.log('Navigation initialized successfully');
});

// Breadcrumb active highlighting
document.addEventListener('DOMContentLoaded', function() {
    // Highlight current page in navigation
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-menu a, .mobile-menu-item');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});