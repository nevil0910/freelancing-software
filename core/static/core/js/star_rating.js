(function () {
    'use strict';

    function renderStarRating(rating, targetEl) {
        if (!targetEl) return;
        const safeRating = Math.max(0, Math.min(5, Number(rating) || 0));
        const full = Math.floor(safeRating);
        const decimal = safeRating - full;
        const empty = 5 - Math.ceil(safeRating);
        const stars = [];

        for (let i = 0; i < full; i++) {
            stars.push('<i class="fas fa-star"></i>');
        }
        if (decimal > 0) {
            stars.push(`<i class="fa-star-partial" style="--star-fill:${Math.round(decimal * 100)}%"></i>`);
        }
        for (let i = 0; i < empty; i++) {
            stars.push('<i class="far fa-star"></i>');
        }

        targetEl.innerHTML = stars.join('');
    }

    window.renderStarRating = renderStarRating;
})();
