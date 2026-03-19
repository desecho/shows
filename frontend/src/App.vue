<template>
  <v-app>
    <v-main>
      <MenuComponent />
      <ErrorBoundary context="Main Application" :allow-retry="true">
        <RouterView />
      </ErrorBoundary>
    </v-main>
    <FooterComponent />
  </v-app>
</template>

<script lang="ts" setup>
import { onMounted } from "vue";

import { initAxios } from "./axios";
import ErrorBoundary from "./components/ErrorBoundary.vue";
import FooterComponent from "./components/FooterComponent.vue";
import MenuComponent from "./components/MenuComponent.vue";
import { useSEO } from "./composables/useSEO";
import { useOrganizationStructuredData } from "./composables/useStructuredData";
import { useAuthStore } from "./stores/auth";
import { useThemeStore } from "./stores/theme";

// Default SEO for the entire application
useSEO({
  title: "Shows",
  description:
    "Track what you watch. Discover what to watch next. Get personalized TV show recommendations and discover your next favorite series.",
  keywords: ["tv shows", "series", "television", "watch", "tracking", "recommendations", "shows"],
  type: "website",
  url: "/",
});

// Organization structured data
useOrganizationStructuredData({
  name: "Shows",
  description:
    "The ultimate TV show tracking platform. Create watchlists, get AI recommendations, and discover your next favorite series.",
  url: "https://shows.samarchyan.me",
  logo: "https://shows.samarchyan.me/img/logo.png",
  sameAs: ["https://github.com/desecho/shows"],
});

const themeStore = useThemeStore();
const authStore = useAuthStore();

onMounted(() => {
  // Initialize Vuetify theme integration
  themeStore.initVuetifyTheme();
  // Initialize theme preferences (auto-restored by plugin, set defaults for new users)
  themeStore.initTheme();

  // Initialize axios with authentication headers
  if (authStore.user.isLoggedIn) {
    initAxios();
  }
});
</script>

<style>
@import "./styles/theme-variables.css";
@import "./styles/dark-theme-components.css";
@import "./styles/dark-theme-custom.css";
@import "./styles/dark-theme-typography.css";
@import "./styles/dark-theme-pagination.css";
@import "./styles/theme-transitions.css";
</style>
