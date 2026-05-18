document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // Animated Counter
    // =========================

    const counters = document.querySelectorAll(".stat-number");

    counters.forEach(counter => {

        const target = Number(counter.innerText.replace(/,/g, ""));

        if (isNaN(target)) return;

        let count = 0;
        const increment = target / 80;

        const interval = setInterval(() => {

            count += increment;

            if (count >= target) {
                counter.innerText = target.toLocaleString();
                clearInterval(interval);
            }
            else {
                counter.innerText = Math.floor(count).toLocaleString();
            }

        }, 20);

    });


    // =========================
    // Active Sidebar Link
    // =========================

    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll(".sidebar-link");

    sidebarLinks.forEach(link => {

        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        }

    });

});