document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Navbar background change on scroll
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled', 'shadow');
        } else {
            navbar.classList.remove('navbar-scrolled', 'shadow');
        }
    });
    
    // Testimonial carousel (if needed)
    // Initialize Bootstrap carousel
    // const testimonialCarousel = new bootstrap.Carousel('#testimonialCarousel', {
    //     interval: 5000,
    //     pause: 'hover'
    // });
});