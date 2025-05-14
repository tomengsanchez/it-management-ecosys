document.addEventListener('DOMContentLoaded', () => {
    const { status, users, categories } = assetDashboardData;

    const createChart = (id, label, dataObj, bgColor = 'rgba(54, 162, 235, 0.6)') => {
        const ctx = document.getElementById(id).getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(dataObj).map(key => {
                    if (id === 'assetUserChart' && !isNaN(key)) {
                        const user = wp.data.select('core').getUser(parseInt(key));
                        return user ? user.name : `User #${key}`;
                    }
                    return key;
                }),
                datasets: [{
                    label,
                    data: Object.values(dataObj),
                    backgroundColor: bgColor
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    };

    createChart('assetStatusChart', 'Assets by Status', status, 'rgba(255, 99, 132, 0.6)');
    createChart('assetUserChart', 'Assets by User', users, 'rgba(255, 206, 86, 0.6)');
    createChart('assetCategoryChart', 'Assets by Category', categories, 'rgba(75, 192, 192, 0.6)');
});


jQuery(document).ready(function($) {
    // Make title field read-only for 'asset' post type if it has a value (i.e., not a new post or auto-draft)
    // This allows setting title programmatically on first save and then making it non-editable.
    // Or, make it always read-only after the first save.
    var $titleInput = $('#titlewrap input#title');
    var $postIDField = $('#post_ID'); // Hidden field with post ID

    // Check if we are on an 'asset' post edit screen and the post has been saved at least once
    if ($('body').hasClass('post-type-asset') && $titleInput.length && $postIDField.length && parseInt($postIDField.val(), 10) > 0) {
        // You can make it readonly based on the title content too, e.g., if it starts with "Asset #"
        // if ($titleInput.val().startsWith('Asset #') || $titleInput.val().startsWith('Asset:')) {
            $titleInput.prop('readonly', true).addClass('am-readonly-title');
            // Optionally, add a message or change appearance more significantly
            // $titleInput.after('<p class="description"><em>Asset title is auto-generated and cannot be changed directly.</em></p>');
        // }
    }
});