<template>
  <section class="landing">
    <div class="hero">
      <h1 class="title">Welcome to Shows</h1>
      <p class="subtitle">Track what you watch. Discover what to watch next.</p>
      <div class="cta">
        <RouterLink class="btn btn-primary" to="/search">Search Shows</RouterLink>
        <RouterLink class="btn btn-primary" to="/trending">Trending Shows</RouterLink>
        <RouterLink v-if="!user.isLoggedIn" class="btn btn-secondary" to="/register"> Create account </RouterLink>
      </div>
    </div>

    <section id="features" class="features">
      <div class="feature">
        <h3>🎬 Smart Search</h3>
        <p>Search by title or actor to quickly find any show you're thinking of.</p>
      </div>
      <div class="feature">
        <h3>📈 Trending Now</h3>
        <p>Stay updated with currently trending shows curated just for you.</p>
      </div>
      <div class="feature">
        <h3>🤖 AI Recommendations</h3>
        <p>Get personalized show suggestions based on your taste and watch history.</p>
      </div>
      <div class="feature">
        <h3>🎯 Custom Watchlist</h3>
        <p>Organize your watchlist in a custom order — prioritize what matters most to you.</p>
      </div>
      <div class="feature">
        <h3>🔗 Share Lists</h3>
        <p>Publish your lists with shareable links — and share watched shows to X.</p>
      </div>
      <div class="feature">
        <h3>📺 Streaming Availability</h3>
        <p>Instantly see where to stream any show on your list.</p>
      </div>
      <div class="feature">
        <h3>🔒 Privacy Settings</h3>
        <p>Control your visibility and choose what others can see.</p>
      </div>
      <div class="feature">
        <h3>🌙 Dark Mode</h3>
        <p>Enjoy a sleek dark UI that's easy on the eyes — day or night.</p>
      </div>
      <div class="feature">
        <h3>📊 Stats & Insights</h3>
        <p>
          At‑a‑glance totals, time watched, ratings, preferences, top genres/people, monthly trends — plus a
          Year‑in‑Review with milestones.
        </p>
      </div>
      <div class="feature">
        <h3>📱 Mobile‑friendly</h3>
        <p>
          Built with a responsive, mobile‑first layout for a great experience on phones, tablets, and desktops — with
          fast navigation and accessible controls.
        </p>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia";

import { useSEO } from "../composables/useSEO";
import { useAuthStore } from "../stores/auth";

// SEO for landing page
useSEO({
  title: "Welcome to Shows",
  description:
    "Track what you watch. Discover what to watch next. Search shows, get AI recommendations, and discover your perfect watchlist on Shows.",
  keywords: [
    "show tracker",
    "TV show tracker",
    "watchlist",
    "show recommendations",
    "AI show suggestions",
    "trending shows",
    "show search",
  ],
  type: "website",
  url: "/",
});

const { user } = storeToRefs(useAuthStore());
</script>

<style scoped>
.landing {
  display: grid;
  place-items: center;
  min-height: calc(100vh - 64px);
  padding: 48px 16px;
}

.hero {
  text-align: center;
  max-width: 820px;
}

.title {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 800;
  color: #4b3fb8;
  letter-spacing: -0.02em;
}

.subtitle {
  margin-top: 12px;
  font-size: 1.125rem;
  color: #555;
}

.cta {
  display: inline-flex;
  gap: 12px;
  margin-top: 24px;
}

.btn {
  padding: 10px 16px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
}

.btn-primary {
  background: #5a67d8;
  color: #fff;
}

.btn-secondary {
  background: #ede9fe;
  color: #5b21b6;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  padding: 4rem 2rem;
}
.feature {
  padding: 2rem;
  border-radius: 10px;
}
.feature h3 {
  margin-top: 0;
  color: #e50914;
}
</style>
