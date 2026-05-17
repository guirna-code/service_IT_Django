document.addEventListener("DOMContentLoaded", function () {
    const navbar = document.querySelector(".page-navbar");

    if (navbar) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 8) {
                navbar.style.background = "rgba(16, 17, 20, 0.94)";
                navbar.style.boxShadow = "0 10px 30px rgba(0, 0, 0, 0.18)";
            } else {
                navbar.style.background = "rgba(16, 17, 20, 0.86)";
                navbar.style.boxShadow = "none";
            }
        });
    }

    setTimeout(function () {
        document.querySelectorAll(".alert.show").forEach(function (alertEl) {
            if (window.bootstrap) {
                bootstrap.Alert.getOrCreateInstance(alertEl).close();
            } else {
                alertEl.style.display = "none";
            }
        });
    }, 4000);
});
