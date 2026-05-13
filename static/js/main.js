document.addEventListener("DOMContentLoaded", function () {
    // Navbar shadow on scroll
    const navbar = document.querySelector(".page-navbar");
    if (navbar) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 8) {
                navbar.style.background = "rgba(15, 15, 18, 0.92)";
                navbar.style.boxShadow = "0 10px 30px rgba(0, 0, 0, 0.18)";
            } else {
                navbar.style.background = "rgba(15, 15, 18, 0.82)";
                navbar.style.boxShadow = "none";
            }
        });
    }

    // Auto-close mobile sidebar after click
    const mobileLinks = document.querySelectorAll(".offcanvas-sidebar .nav-link");
    const sidebar = document.getElementById("sidebarCanvas");

    mobileLinks.forEach(link => {
        link.addEventListener("click", () => {
            if (sidebar && window.bootstrap) {
                const instance = bootstrap.Offcanvas.getInstance(sidebar) || new bootstrap.Offcanvas(sidebar);
                instance.hide();
            }
        });
    });

    // Ripple effect on buttons
    document.querySelectorAll(".btn").forEach(button => {
        button.addEventListener("click", function (e) {
            const circle = document.createElement("span");
            const diameter = Math.max(this.clientWidth, this.clientHeight);
            const radius = diameter / 2;

            circle.style.width = circle.style.height = `${diameter}px`;
            circle.style.left = `${e.clientX - this.getBoundingClientRect().left - radius}px`;
            circle.style.top = `${e.clientY - this.getBoundingClientRect().top - radius}px`;
            circle.classList.add("ripple-effect");

            const existing = this.querySelector(".ripple-effect");
            if (existing) existing.remove();

            this.appendChild(circle);
        });
    });

    // Reveal animation
    const reveals = document.querySelectorAll(".reveal");
    if (reveals.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("active");
                }
            });
        }, { threshold: 0.12 });

        reveals.forEach(el => observer.observe(el));
    }

    // Auto-hide alerts
    setTimeout(() => {
        document.querySelectorAll(".alert.show").forEach(alertEl => {
            if (window.bootstrap) {
                const alertInstance = bootstrap.Alert.getOrCreateInstance(alertEl);
                alertInstance.close();
            } else {
                alertEl.style.display = "none";
            }
        });
    }, 4000);
});
document.addEventListener("DOMContentLoaded", function () {
    const navbar = document.querySelector(".page-navbar");

    if (navbar) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 8) {
                navbar.style.background = "rgba(15, 15, 18, 0.94)";
                navbar.style.boxShadow = "0 10px 30px rgba(0, 0, 0, 0.18)";
            } else {
                navbar.style.background = "rgba(15, 15, 18, 0.82)";
                navbar.style.boxShadow = "none";
            }
        });
    }
});