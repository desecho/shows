<template>
  <v-container>
    <v-row>
      <v-col cols="9">
        <p>Create show lists "Watched", "Watching", and "To Watch", rate shows, and add comments.</p>
        <br />
        <h3>Features</h3>
        <ul>
          <li>Search for shows by title or actor</li>
          <li>Get a list of currently trending shows</li>
          <li>AI-powered recommendations</li>
          <li>Stats</li>
          <li>Add custom order for the "To Watch" list</li>
          <li>Share your lists online</li>
          <li>Share to X (watched shows with a rating or comment)</li>
          <li>See where you can stream a show</li>
          <li>Privacy settings.</li>
          <li>Dark mode</li>
          <li>Mobile-friendly responsive design</li>
        </ul>
        <br />
        <h3>Tips</h3>
        <ul>
          <li>You can see the original title when you hover over the show title</li>
          <li>You can only add custom order on the Gallery page for the "To Watch" list</li>
          <li>To be able to see where you can stream a show, you need to set your country in preferences</li>
        </ul>
        <br />
        <h3>Streaming data</h3>
        <p>
          Streaming data is currently only available in Canada, the United States are supported. You can
          <a :href="`mailto:${email}`">email me</a> to request support for your country.
        </p>
        <br />
        <h3>Rating system</h3>
        <ul>
          <li>1 — Awful</li>
          <li>2 — Bad</li>
          <li>3 — Ok</li>
          <li>4 — Good</li>
          <li>5 — Excellent</li>
        </ul>
        <br />
        <h3>APIs used</h3>
        <ul>
          <li>
            <a href="https://www.themoviedb.org/" target="_blank">TMDB</a>
          </li>
          <li>
            <a href="https://www.omdbapi.com/" target="_blank">OMDb</a>
          </li>
        </ul>
        <br />
        <h3>Import/Export data</h3>
        <p>
          If you would like to import or export data, please
          <a :href="`mailto:${email}`">email me</a>.
        </p>
        <br />
        <h3>Source code</h3>
        <p>
          The source code is available
          <a href="https://github.com/desecho/shows" target="_blank">on GitHub</a>.
        </p>
        <br />
        <h3>Contact info</h3>
        <p>
          If you have problems with account activation or other issues, questions or feedback please
          <a :href="`mailto:${email}`">email me</a>.
        </p>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>
import { useSEO } from "../composables/useSEO";
import { ADMIN_EMAIL } from "../const";

// SEO for about page
useSEO({
  title: "About Shows",
  description:
    "Learn about Shows - the ultimate TV show tracking platform. Create watchlists, get AI recommendations, and discover your next favorite show.",
  keywords: ["about shows", "show tracking features", "TV show database", "watchlist app", "show recommendations"],
  type: "article",
  url: "/about",
});

const email = ADMIN_EMAIL;
</script>
