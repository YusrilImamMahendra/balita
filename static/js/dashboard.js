document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    if (document.getElementById('statusChart')) {
        const ctx = document.getElementById('statusChart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: JSON.parse(document.getElementById('chart-labels').textContent),
                datasets: [{
                    data: JSON.parse(document.getElementById('chart-data').textContent),
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.7)',
                        'rgba(255, 193, 7, 0.7)',
                        'rgba(220, 53, 69, 0.7)',
                        'rgba(23, 162, 184, 0.7)'
                    ]
                }]
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const profileIcon = document.getElementById('profile-icon');
    const dropdownMenu = document.getElementById('dropdown-menu');

    profileIcon.addEventListener('click', function () {
        dropdownMenu.classList.toggle('hidden');
    });
});