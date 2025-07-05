// Main JavaScript file for ChronoScript.AI landing page

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

// Stagger animation observer
const staggerObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

// Observe all fade-in-up and stagger animation elements
document.addEventListener('DOMContentLoaded', () => {
    const fadeElements = document.querySelectorAll('.fade-in-up');
    fadeElements.forEach(el => observer.observe(el));
    
    // Observe stagger animation elements
    const staggerElements = document.querySelectorAll('.stagger-animation');
    staggerElements.forEach(el => staggerObserver.observe(el));
});

// Mobile menu toggle
const mobileMenuButton = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');

if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener('click', () => {
        mobileMenu.classList.toggle('hidden');
    });
}

// Contact form handling
const contactForm = document.getElementById('contactForm');
const formMessages = document.getElementById('form-messages');
const submitBtn = document.getElementById('submitBtn');

if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Disable submit button and show loading state
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';
        
        // Hide previous messages
        formMessages.classList.add('hidden');
        
        try {
            const formData = new FormData(contactForm);
            
            const response = await fetch('/submit_contact', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                formMessages.textContent = result.message;
                formMessages.className = 'mb-4 p-3 rounded-md bg-green-100 text-green-800 border border-green-200';
                formMessages.classList.remove('hidden');
                
                // Reset form
                contactForm.reset();
            } else {
                // Show error message
                formMessages.textContent = result.error || 'An error occurred. Please try again.';
                formMessages.className = 'mb-4 p-3 rounded-md bg-red-100 text-red-800 border border-red-200';
                formMessages.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            formMessages.textContent = 'An error occurred. Please try again.';
            formMessages.className = 'mb-4 p-3 rounded-md bg-red-100 text-red-800 border border-red-200';
            formMessages.classList.remove('hidden');
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send Message';
        }
    });
}

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offsetTop = target.offsetTop - 64; // Account for fixed navbar
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
        // Close mobile menu if open
        if (mobileMenu) {
            mobileMenu.classList.add('hidden');
        }
    });
});

// Active navigation highlighting and navbar background change
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('nav a[href^="#"]');
    
    // Change navbar background based on scroll position
    if (window.pageYOffset > 50) {
        navbar.className = navbar.className.replace('bg-white/20', 'bg-white/90');
    } else {
        navbar.className = navbar.className.replace('bg-white/90', 'bg-white/20');
    }
    
    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        const sectionHeight = section.clientHeight;
        if (window.pageYOffset >= sectionTop && window.pageYOffset < sectionTop + sectionHeight) {
            current = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('text-blue-600');
        link.classList.add('text-gray-700');
        if (link.getAttribute('href') === `#${current}`) {
            link.classList.remove('text-gray-700');
            link.classList.add('text-blue-600');
        }
    });
});
