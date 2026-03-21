<template>
  <div class="show-detail-view">
    <div class="container">
      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <v-progress-circular indeterminate color="primary" size="64" class="loading-spinner" />
        <p class="loading-text">Loading show details...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-container">
        <v-alert type="error" title="Error Loading Show" :text="error" class="error-alert" />
        <v-btn color="primary" class="retry-btn" @click="fetchShowDetails"> Try Again </v-btn>
      </div>

      <!-- Show Details -->
      <div v-else-if="showData" class="show-detail">
        <div class="show-header">
          <div class="poster-section">
            <div class="poster-container">
              <v-lazy-image
                v-if="showData.show.hasPoster"
                :src="showData.show.posterBig"
                :alt="showData.show.title"
                :title="showData.show.titleOriginal"
                class="show-poster"
              />
              <div v-else class="no-poster">
                <v-icon icon="mdi-television" size="80" color="grey" />
                <p>No Poster Available</p>
              </div>
            </div>
          </div>

          <div class="show-info">
            <div class="title-section">
              <h1 class="show-title">{{ showData.show.title }}</h1>
              <h2 v-if="showData.show.titleOriginal !== showData.show.title" class="original-title">
                {{ showData.show.titleOriginal }}
              </h2>
            </div>

            <!-- Add to List Buttons for Authenticated Users -->
            <div v-if="isLoggedIn && !userRecord" class="add-to-list-section">
              <v-btn
                v-if="showData.show.isReleased"
                color="primary"
                :disabled="addingToList"
                class="add-btn"
                @click="addToList(listWatchedId)"
              >
                <v-icon icon="mdi-eye" />
                Add to Watched
              </v-btn>
              <v-btn
                v-else
                disabled
                color="primary"
                variant="outlined"
                class="add-btn disabled-watched-btn"
                title="Cannot add unreleased show to watched list"
              >
                <v-icon icon="mdi-eye-off-outline" />
                Not Yet Released
              </v-btn>
              <v-btn color="info" :disabled="addingToList" class="add-btn" @click="addToList(listWatchingId)">
                <v-icon icon="mdi-eye-check" />
                Add to Watching
              </v-btn>
              <v-btn color="secondary" :disabled="addingToList" class="add-btn" @click="addToList(listToWatchId)">
                <v-icon icon="mdi-eye-off" />
                Add to To Watch
              </v-btn>
            </div>

            <!-- User's Record Status -->
            <div v-else-if="userRecord" class="user-record-section">
              <v-chip
                :color="
                  userRecord.listId === listWatchedId
                    ? 'success'
                    : userRecord.listId === listWatchingId
                      ? 'info'
                      : 'warning'
                "
                variant="elevated"
                class="record-chip"
              >
                <v-icon
                  :icon="
                    userRecord.listId === listWatchedId
                      ? 'mdi-eye'
                      : userRecord.listId === listWatchingId
                        ? 'mdi-eye-check'
                        : 'mdi-eye-off'
                  "
                />
                {{
                  userRecord.listId === listWatchedId
                    ? "In Watched List"
                    : userRecord.listId === listWatchingId
                      ? "In Watching List"
                      : "In To Watch List"
                }}
              </v-chip>

              <!-- Rating Display -->
              <div v-if="userRecord.listId === listWatchedId && userRecord.rating" class="rating-section">
                <star-rating :rating="userRecord.rating" :star-size="25" :show-rating="false" :read-only="true" />
                <span class="rating-text">Your Rating</span>
              </div>
            </div>

            <!-- Show Metadata -->
            <div class="metadata-grid">
              <div v-if="showData.show.firstAirDate" class="metadata-item">
                <span class="label">First Air Date:</span>
                <span class="value">{{ showData.show.firstAirDate }}</span>
              </div>
              <div v-if="showData.show.imdbRating" class="metadata-item">
                <span class="label">IMDb Rating:</span>
                <span class="value">{{ showData.show.imdbRating }}/10</span>
              </div>
              <div v-if="showData.show.country" class="metadata-item">
                <span class="label">Country:</span>
                <span class="value">{{ showData.show.country }}</span>
              </div>
              <div v-if="showData.show.writer" class="metadata-item">
                <span class="label">Writer:</span>
                <span class="value">{{ showData.show.writer }}</span>
              </div>
              <div v-if="showData.show.genre" class="metadata-item">
                <span class="label">Genre:</span>
                <span class="value">{{ showData.show.genre }}</span>
              </div>
              <div v-if="showData.show.actors" class="metadata-item">
                <span class="label">Actors:</span>
                <span class="value">{{ showData.show.actors }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Overview -->
        <div v-if="showData.show.overview" class="overview-section">
          <h3>Overview</h3>
          <p class="overview-text">{{ showData.show.overview }}</p>
        </div>

        <!-- External Links -->
        <div class="links-section">
          <h3>External Links</h3>
          <div class="links-grid">
            <a
              v-if="showData.show.homepage"
              :href="showData.show.homepage"
              target="_blank"
              class="external-link website-link"
            >
              <v-icon icon="mdi-web" />
              Official Website
              <v-icon icon="mdi-open-in-new" size="small" />
            </a>
            <a :href="showData.show.imdbUrl" target="_blank" class="external-link imdb-link">
              <span class="imdb-logo"></span>
              IMDb
              <v-icon icon="mdi-open-in-new" size="small" />
            </a>
            <a :href="showData.show.tmdbUrl" target="_blank" class="external-link tmdb-link">
              <span class="tmdb-logo"></span>
              TMDB
              <v-icon icon="mdi-open-in-new" size="small" />
            </a>
          </div>
        </div>

        <!-- Trailers -->
        <div v-if="showData.show.trailers.length > 0" class="trailers-section">
          <h3>Trailers</h3>
          <div class="trailers-grid">
            <a
              v-for="trailer in showData.show.trailers"
              :key="trailer.name"
              :href="trailer.url"
              target="_blank"
              class="trailer-link"
            >
              <v-icon icon="mdi-play" />
              {{ trailer.name }}
              <v-icon icon="mdi-open-in-new" size="small" />
            </a>
          </div>
        </div>

        <!-- Streaming Providers -->
        <div v-if="showData.providerRecords.length > 0" class="providers-section">
          <h3>Stream On</h3>
          <div class="providers-grid">
            <a
              v-for="providerRecord in showData.providerRecords"
              :key="providerRecord.provider.name"
              :href="providerRecord.tmdbWatchUrl"
              target="_blank"
              class="provider-link"
            >
              <v-lazy-image
                :src="providerRecord.provider.logo"
                :alt="providerRecord.provider.name"
                :title="providerRecord.provider.name"
                class="provider-logo"
              />
              <span class="provider-name">{{ providerRecord.provider.name }}</span>
              <v-icon icon="mdi-open-in-new" size="small" />
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import axios, { isAxiosError } from "axios";
import VLazyImage from "v-lazy-image";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import StarRating from "vue-star-rating";

import type { ProviderRecord, RecordType, Show } from "../types";

import { listToWatchId, listWatchedId, listWatchingId } from "../const";
import { getUrl } from "../helpers";
import { useAuthStore } from "../stores/auth";

interface ShowDetailResponse {
  show: Show;
  providerRecords: ProviderRecord[];
  userRecord: RecordType | null;
}

const route = useRoute();
const authStore = useAuthStore();

const loading = ref(true);
const error = ref<string | null>(null);
const showData = ref<ShowDetailResponse | null>(null);
const addingToList = ref(false);

const isLoggedIn = computed(() => authStore.user.isLoggedIn);
const userRecord = computed(() => showData.value?.userRecord || null);

const tmdbId = computed(() => {
  const id = route.params.tmdbId;
  return typeof id === "string" ? parseInt(id, 10) : null;
});

async function fetchShowDetails(): Promise<void> {
  if (!tmdbId.value) {
    error.value = "Invalid show ID";
    loading.value = false;
    return;
  }

  try {
    loading.value = true;
    error.value = null;

    const response = await axios.get<ShowDetailResponse>(getUrl(`show/${tmdbId.value}/`));

    showData.value = response.data;
  } catch (err) {
    console.error("Error fetching show details:", err);
    if (isAxiosError(err) && err.response?.status === 404) {
      error.value = "Show not found";
    } else {
      error.value = "Failed to load show details. Please try again.";
    }
  } finally {
    loading.value = false;
  }
}

async function addToList(listId: number): Promise<void> {
  if (!tmdbId.value || !isLoggedIn.value) {
    return;
  }

  try {
    addingToList.value = true;

    await axios.post(getUrl("add-to-list-from-db/"), {
      showId: tmdbId.value,
      listId,
    });

    // Refresh show data to get updated user record
    void fetchShowDetails();
  } catch (err) {
    console.error("Error adding to list:", err);

    // Check if it's an unreleased show error
    if (
      isAxiosError(err) &&
      err.response?.data &&
      typeof err.response.data === "object" &&
      "status" in err.response.data &&
      (err.response.data as { status: unknown }).status === "unreleased"
    ) {
      error.value = "Cannot add unreleased show to watched list. You can add it to your 'To Watch' list instead.";
    } else {
      error.value = "Failed to add show to list. Please try again.";
    }
  } finally {
    addingToList.value = false;
  }
}

onMounted(() => {
  void fetchShowDetails();
});
</script>

<style scoped>
.show-detail-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  text-align: center;
}

.loading-text {
  margin-top: 16px;
  font-size: 1.2rem;
  color: #666;
}

.error-alert {
  margin-bottom: 16px;
}

.show-detail {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.show-header {
  display: flex;
  gap: 32px;
  padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.poster-section {
  flex-shrink: 0;
}

.poster-container {
  width: 300px;
  position: relative;
}

.show-poster {
  width: 100%;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.no-poster {
  width: 300px;
  height: 450px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.show-info {
  flex: 1;
  min-width: 0;
}

.title-section {
  margin-bottom: 24px;
}

.show-title {
  font-size: 2.5rem;
  font-weight: 800;
  margin: 0 0 8px 0;
  line-height: 1.2;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.original-title {
  font-size: 1.4rem;
  font-weight: 400;
  margin: 0;
  opacity: 0.9;
  font-style: italic;
}

.add-to-list-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.add-btn {
  font-weight: 600;
}

.disabled-watched-btn {
  opacity: 0.7;
  cursor: not-allowed;
}

.user-record-section {
  margin-bottom: 24px;
}

.record-chip {
  margin-bottom: 16px;
}

.rating-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rating-text {
  font-weight: 500;
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.metadata-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.label {
  font-weight: 600;
  min-width: 100px;
  opacity: 0.9;
}

.value {
  flex: 1;
}

.overview-section,
.links-section,
.trailers-section,
.providers-section {
  padding: 32px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.overview-section h3,
.links-section h3,
.trailers-section h3,
.providers-section h3 {
  margin: 0 0 16px 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #333;
}

.overview-text {
  font-size: 1.1rem;
  line-height: 1.6;
  color: #555;
  margin: 0;
}

.links-grid,
.trailers-grid {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.external-link,
.trailer-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  text-decoration: none !important;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.external-link:hover,
.trailer-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
}

.imdb-logo,
.tmdb-logo {
  width: 24px;
  height: 24px;
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.imdb-logo {
  background-image: url("/img/imdb.png");
}

.tmdb-logo {
  background-image: url("/img/tmdb.svg");
}

.providers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.provider-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  text-decoration: none !important;
  color: #333 !important;
  transition: all 0.3s ease;
}

.provider-link:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
}

.provider-logo {
  width: 40px;
  height: 40px;
  border-radius: 6px;
}

.provider-name {
  flex: 1;
  font-weight: 500;
}

@media (max-width: 768px) {
  .container {
    padding: 16px;
  }

  .show-header {
    flex-direction: column;
    padding: 24px;
    text-align: center;
  }

  .poster-container {
    width: 250px;
    margin: 0 auto;
  }

  .show-title {
    font-size: 2rem;
  }

  .metadata-grid {
    grid-template-columns: 1fr;
  }

  .links-grid,
  .trailers-grid {
    flex-direction: column;
  }

  .providers-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .poster-container {
    width: 200px;
  }

  .show-title {
    font-size: 1.6rem;
  }

  .overview-section,
  .links-section,
  .trailers-section,
  .providers-section {
    padding: 20px;
  }
}
</style>
