<template>
  <div class="results">
    <div v-for="show in shows" v-show="!show.hidden" :key="show.id" class="show">
      <div class="poster-wrapper">
        <div class="poster">
          <div v-if="isLoggedIn" class="add-to-list-buttons">
            <a
              v-show="show.isReleased"
              href="javascript:void(0)"
              title='Add to the list "Watched"'
              @click="addToListFromDb(show, listWatchedId)"
            >
              <v-icon icon="mdi-eye" />
            </a>
            <a
              href="javascript:void(0)"
              title='Add to the list "Watching"'
              @click="addToListFromDb(show, listWatchingId)"
            >
              <v-icon icon="mdi-eye-check" />
            </a>
            <a
              href="javascript:void(0)"
              title='Add to the list "To Watch"'
              @click="addToListFromDb(show, listToWatchId)"
              ><v-icon icon="mdi-eye-off"
            /></a>
          </div>
          <a :href="`/show/${show.id}`" target="_blank">
            <v-lazy-image
              :srcset="getSrcSet(show.poster, show.poster2x)"
              :src="show.poster2x"
              :title="show.titleOriginal"
              :alt="show.title"
            />
          </a>
        </div>
      </div>
      <div class="show-content">
        <div class="title">{{ show.title }}</div>
        <div v-show="show.firstAirDate" class="details">
          {{ show.firstAirDate }}
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import axios from "axios";
import VLazyImage from "v-lazy-image";

import type { AddToListFromDbResponseData, ShowPreview } from "../types";
import type { AxiosError } from "axios";

import { listToWatchId, listWatchedId, listWatchingId } from "../const";
import { getSrcSet, getUrl } from "../helpers";
import { useAuthStore } from "../stores/auth";
import { useRecordsStore } from "../stores/records";
import { $toast } from "../toast";

defineProps<{
  shows: ShowPreview[];
}>();

const { user } = useAuthStore();
const isLoggedIn = user.isLoggedIn;

async function addToListFromDb(show: ShowPreview, listId: number): Promise<void> {
  await axios
    .post(getUrl("add-to-list-from-db/"), {
      showId: show.id,
      listId,
    })
    .then((response) => {
      const data = response.data as AddToListFromDbResponseData;
      if (data.status === "not_found") {
        $toast.error("Show is not found in the database");
        return;
      }
      show.hidden = true;
    })
    .catch(() => {
      $toast.error("Error adding a show");
    });
  const { reloadRecords } = useRecordsStore();
  reloadRecords()
    .then(() => {
      console.log("Records reloaded");
    })
    .catch((error: AxiosError) => {
      console.log(error);
      $toast.error("Error reloading records");
    });
}
</script>

<style scoped>
.results {
  clear: both;
  margin-top: 24px;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 20px;
}

.show {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
  min-height: auto;
  width: auto;
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);

    .add-to-list-buttons {
      opacity: 1;
    }

    .poster img {
      transform: scale(1.02);
    }
  }
}

.poster-wrapper {
  height: 255px;
  overflow: hidden;
  border-radius: 12px 12px 0 0;
}

.poster {
  position: relative;
  height: 100%;
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 12px 12px 0 0;
    transition: transform 0.3s ease;
  }
}

.add-to-list-buttons {
  position: absolute;
  right: 12px;
  bottom: 12px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 6px;
  opacity: 0;
  transition: all 0.3s ease;
  display: flex;
  gap: 4px;
  z-index: 10;

  a {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.1);
    color: #333;
    transition: all 0.2s ease;
    margin: 0;
    text-decoration: none;
    cursor: pointer;

    &:hover,
    &:focus {
      background: rgba(0, 0, 0, 0.2);
      transform: scale(1.1);
    }

    &:active {
      transform: scale(0.95);
    }

    .v-icon {
      font-size: 18px;
      pointer-events: none;
    }
  }
}

/* Touch device support */
@media (hover: none) and (pointer: coarse) {
  .add-to-list-buttons {
    opacity: 1;
    background: rgba(255, 255, 255, 0.9);
  }
}

.show-content {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  width: auto;
}

.title {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.4;
  color: #2d3748;
  display: block;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.details {
  font-size: 0.875rem;
  color: #718096;
  font-weight: 500;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .results {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
    margin-top: 20px;
  }

  .poster-wrapper {
    height: 210px;
  }

  .show-content {
    padding: 12px;
  }

  .title {
    font-size: 0.9rem;
  }

  .details {
    font-size: 0.8rem;
  }

  .add-to-list-buttons {
    opacity: 1; /* Always visible on mobile/touch devices */
    right: 8px;
    bottom: 8px;
    padding: 4px;

    a {
      width: 28px;
      height: 28px;

      .v-icon {
        font-size: 16px;
      }
    }
  }
}

@media (max-width: 480px) {
  .results {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
  }

  .poster-wrapper {
    height: 180px;
  }
}
</style>
