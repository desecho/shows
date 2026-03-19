import axios from "axios";
import { jwtDecode } from "jwt-decode";
import { defineStore } from "pinia";

import type { JWTDecoded } from "../types";
import type { TokenData, TokenRefreshData, UserStore } from "./types";

import { initAxios } from "../axios";
import { getUrl } from "../helpers";
import { router } from "../router";
import { isValidToken } from "../types/common";

const userDefault: UserStore = {
    isLoggedIn: false,
};

export const useAuthStore = defineStore("auth", {
    state: () => ({
        user: userDefault,
    }),
    persist: true,
    actions: {
        async login(username: string, password: string) {
            const response = await axios.post(getUrl("token/"), {
                username,
                password,
            });
            const data = response.data as TokenData;
            this.user = {
                refreshToken: data.refresh,
                accessToken: data.access,
                isLoggedIn: true,
                username,
            };
            initAxios();
            void router.push("/");
        },
        // This function needs to be called only when user is logged in
        async refreshToken() {
            if (!isValidToken(this.user.refreshToken)) {
                this.logout();
                return;
            }

            const decodedToken: JWTDecoded = jwtDecode(this.user.refreshToken);
            // If refresh token expired we log the user out
            if (decodedToken.exp < Date.now() / 1000) {
                this.logout();
                return;
            }

            const response = await axios.post(getUrl("token/refresh/"), {
                refresh: this.user.refreshToken,
            });
            const data = response.data as TokenRefreshData;
            this.user.accessToken = data.access;
            initAxios();
        },
        logout() {
            // Reset to a fresh object to avoid shared reference issues
            this.user = { isLoggedIn: false };
            localStorage.removeItem("user");
            // Clear Authorization header explicitly
            delete axios.defaults.headers.common["Authorization"];
            initAxios();
            void router.push("/");
        },
    },
});
