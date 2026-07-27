+++
title = 'Losowa restauracja w Poznaniu'
date = 2026-07-27T00:00:00+02:00
draft = false
showToc = false
+++

Nie wiesz gdzie zjeść? Kliknij przycisk, a strona wybierze losową restaurację z listy Visit Poznań.

<div id="restaurant-picker" style="margin: 2rem 0; padding: 1.5rem; border: 1px solid var(--border); border-radius: 12px;">
  <button id="pick-restaurant" type="button" style="padding: 0.7rem 1rem; border-radius: 8px; border: 1px solid var(--border); cursor: pointer;">
    Wylosuj restaurację
  </button>

  <p id="restaurant-status" style="margin-top: 1rem;">Ładowanie listy restauracji…</p>

  <div id="restaurant-result" hidden style="margin-top: 1rem;">
    <h2 id="restaurant-name" style="margin-bottom: 0.5rem;"></h2>
    <p><a id="restaurant-link" href="#" target="_blank" rel="noopener noreferrer">Otwórz stronę restauracji</a></p>
  </div>
</div>

<script>
(() => {
  const button = document.getElementById('pick-restaurant');
  const status = document.getElementById('restaurant-status');
  const result = document.getElementById('restaurant-result');
  const name = document.getElementById('restaurant-name');
  const link = document.getElementById('restaurant-link');
  let restaurants = [];

  function pickRestaurant() {
    if (!restaurants.length) return;

    const restaurant = restaurants[Math.floor(Math.random() * restaurants.length)];
    name.textContent = restaurant.name;
    link.href = restaurant.url;
    status.textContent = '';
    result.hidden = false;
  }

  button.disabled = true;

  const pageUrl = window.location.pathname.endsWith('/')
    ? window.location.href
    : `${window.location.href}/`;

  fetch(new URL('../restaurants.json', pageUrl))
    .then((response) => {
      if (!response.ok) throw new Error('Could not load restaurants.json');
      return response.json();
    })
    .then((data) => {
      restaurants = data;
      button.disabled = false;
      status.textContent = `Gotowe — ${restaurants.length} restauracji na liście.`;
      pickRestaurant();
    })
    .catch(() => {
      status.textContent = 'Nie udało się załadować listy restauracji.';
    });

  button.addEventListener('click', pickRestaurant);
})();
</script>
