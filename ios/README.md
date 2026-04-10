# Shows iOS App

SwiftUI iOS client for the `shows` Django backend.

## Features

- JWT login against the existing backend
- Three synced lists: `Watched`, `Watching`, and `To Watch`
- Search by show title or actor via the backend TMDB search
- AI recommendations with genre, year, rating, and count filters
- Add, move, and remove shows using the existing list endpoints

## Requirements

- iOS 17.0+
- Xcode 15.0+

## Setup

1. Start the local backend on `http://127.0.0.1:8000`.
2. Open `ShowsApp.xcodeproj` in Xcode.
3. Run the app in an iOS 17 simulator.

## Backend Endpoints Used

- `POST /token/`
- `POST /token/refresh/`
- `GET /records/`
- `DELETE /remove-record/{recordId}/`
- `POST /add-to-list/{showId}/`
- `POST /add-to-list-from-db/`
- `GET /search/`
- `GET /recommendations/`

## Notes

- Debug builds point at `http://127.0.0.1:8000`.
- Release builds point at `https://api.shows.samarchyan.me`.
- The app stores JWT tokens in `UserDefaults` and refreshes access tokens automatically when possible.
