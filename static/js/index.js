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

// Hero Image Carousel functionality
document.addEventListener('DOMContentLoaded', () => {
    const carousel = document.getElementById('heroCarousel');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const dots = document.querySelectorAll('.carousel-dot');
    
    if (!carousel || !prevBtn || !nextBtn) return;
    
    let currentSlide = 0;
    const totalSlides = 3;
    
    // Function to update carousel position
    function updateCarousel() {
        const translateX = -currentSlide * 100;
        carousel.style.transform = `translateX(${translateX}%)`;
        
        // Update dots
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === currentSlide);
        });
    }
    
    // Next slide function
    function nextSlide() {
        currentSlide = (currentSlide + 1) % totalSlides;
        updateCarousel();
    }
    
    // Previous slide function
    function prevSlide() {
        currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
        updateCarousel();
    }
    
    // Event listeners
    nextBtn.addEventListener('click', () => {
        carousel.classList.remove('auto-play');
        nextSlide();
    });
    
    prevBtn.addEventListener('click', () => {
        carousel.classList.remove('auto-play');
        prevSlide();
    });
    
    // Dot navigation
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            carousel.classList.remove('auto-play');
            currentSlide = index;
            updateCarousel();
        });
    });
    
    // Image click to advance to next slide
    const carouselImages = carousel.querySelectorAll('.carousel-slide img');
    carouselImages.forEach(img => {
        img.addEventListener('click', () => {
            carousel.classList.remove('auto-play');
            nextSlide();
        });
        // Add cursor pointer to indicate clickability
        img.style.cursor = 'pointer';
    });
    
    // Initialize carousel
    updateCarousel();
});

// === HERO BACKGROUND ANIMATION === 
// Responsive 3D parallax animation with mobile optimization
document.addEventListener('DOMContentLoaded', () => {
    const layers = document.querySelectorAll('.hero-background .layer');
    
    if (layers.length > 0) {
        // Check if user prefers reduced motion
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        // Device and screen size detection
        const isMobile = window.innerWidth <= 768;
        const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
        const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        
        // Responsive animation parameters
        const getAnimationParams = () => {
            if (isMobile) {
                return {
                    depthMultiplier: 0.5,
                    scaleMultiplier: 0.02,
                    rotationMultiplier: 0.1,
                    throttleDelay: 16 // ~60fps
                };
            } else if (isTablet) {
                return {
                    depthMultiplier: 0.75,
                    scaleMultiplier: 0.03,
                    rotationMultiplier: 0.15,
                    throttleDelay: 12 // ~83fps
                };
            } else {
                return {
                    depthMultiplier: 1,
                    scaleMultiplier: 0.04,
                    rotationMultiplier: 0.2,
                    throttleDelay: 8 // ~125fps
                };
            }
        };
        
        const params = getAnimationParams();
        
        // Throttle function for performance
        let isThrottled = false;
        const throttle = (func, delay) => {
            if (isThrottled) return;
            isThrottled = true;
            setTimeout(() => {
                func();
                isThrottled = false;
            }, delay);
        };
        
        // Animation function
        const animateLayers = (x, y) => {
            if (prefersReducedMotion) return;
            
            layers.forEach((layer, i) => {
                const depth = (i + 1) * 20 * params.depthMultiplier;
                const scale = 1 + i * params.scaleMultiplier;
                const rotateX = y * depth * params.rotationMultiplier;
                const rotateY = x * depth * params.rotationMultiplier;
                
                layer.style.transform = `
                    translate3d(${x * depth}px, ${y * depth}px, ${-depth * 2}px)
                    scale(${scale})
                    rotateX(${rotateX}deg)
                    rotateY(${rotateY}deg)
                `;
            });
        };
        
        // Mouse move handler for desktop
        if (!isTouch) {
            document.addEventListener('mousemove', (e) => {
                const x = (e.clientX / window.innerWidth - 0.5) * 2;
                const y = (e.clientY / window.innerHeight - 0.5) * 2;
                
                throttle(() => animateLayers(x, y), params.throttleDelay);
            });
        }
        
        // Touch/orientation handlers for mobile
        if (isTouch) {
            // Device orientation for mobile tilt effect
            if (window.DeviceOrientationEvent) {
                window.addEventListener('deviceorientation', (e) => {
                    if (prefersReducedMotion) return;
                    
                    const x = (e.gamma || 0) / 90; // -1 to 1 range
                    const y = (e.beta || 0) / 90;  // -1 to 1 range
                    
                    throttle(() => animateLayers(x * 0.5, y * 0.5), params.throttleDelay);
                });
            }
            
            // Touch move for mobile devices
            let touchStartX = 0;
            let touchStartY = 0;
            
            document.addEventListener('touchstart', (e) => {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
            });
            
            document.addEventListener('touchmove', (e) => {
                if (e.touches.length === 1) {
                    const touch = e.touches[0];
                    const x = ((touch.clientX - touchStartX) / window.innerWidth) * 2;
                    const y = ((touch.clientY - touchStartY) / window.innerHeight) * 2;
                    
                    throttle(() => animateLayers(x * 0.3, y * 0.3), params.throttleDelay);
                }
            });
        }
        
        // Entrance animation with responsive timing
        const animateEntrance = () => {
            layers.forEach((layer, i) => {
                const delay = isMobile ? 50 + i * 100 : 50 + i * 150;
                const duration = isMobile ? '1.2s' : '1.5s';
                
                if (layer.classList.contains('layer1')) {
                    // Layer 1 starts from above and slides down
                    layer.style.transform = `translate3d(0, -50vh, 0) scale(1)`;
                    layer.style.transition = `transform ${duration} cubic-bezier(.55,.5,.45,.5)`;
                    // Start immediately, no delay for first layer
                    setTimeout(() => {
                        layer.style.transform = '';
                    }, 10);
                } else {
                    // Other layers start from below and slide up
                    layer.style.transform = `translate3d(0, 100vh, 0) scale(1)`;
                    layer.style.transition = `transform ${duration} cubic-bezier(.55,.5,.45,.5)`;
                    setTimeout(() => {
                        layer.style.transform = '';
                    }, delay);
                }
            });
        };
        
        // Handle window resize
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                // Reset transforms on resize
                layers.forEach(layer => {
                    layer.style.transform = '';
                });
                
                // Update animation parameters
                const newParams = getAnimationParams();
                Object.assign(params, newParams);
            }, 250);
        });
        
        // Handle visibility change (pause animation when tab is not active)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Pause animation
                layers.forEach(layer => {
                    layer.style.animationPlayState = 'paused';
                });
            } else {
                // Resume animation
                layers.forEach(layer => {
                    layer.style.animationPlayState = 'running';
                });
            }
        });
        
        // Initialize entrance animation immediately
        if (!prefersReducedMotion) {
            // Start animation immediately when page loads
            requestAnimationFrame(() => {
                animateEntrance();
            });
        } else {
            // For reduced motion, just ensure layers are visible
            layers.forEach(layer => {
                layer.style.transform = '';
                layer.style.transition = 'transform 0.5s ease-out';
            });
        }
    }
});
