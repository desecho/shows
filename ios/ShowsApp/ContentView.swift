import SwiftUI

struct ContentView: View {
    @StateObject private var apiService = APIService()

    var body: some View {
        Group {
            if apiService.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .environmentObject(apiService)
    }
}

private struct MainTabView: View {
    var body: some View {
        TabView {
            ShowListView(listType: .watched)
                .tabItem {
                    Label("Watched", systemImage: ListType.watched.systemImage)
                }

            ShowListView(listType: .watching)
                .tabItem {
                    Label("Watching", systemImage: ListType.watching.systemImage)
                }

            ShowListView(listType: .toWatch)
                .tabItem {
                    Label("To Watch", systemImage: ListType.toWatch.systemImage)
                }

            TrendingView()
                .tabItem {
                    Label("Trending", systemImage: "flame.fill")
                }

            SearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }

            RecommendationsView()
                .tabItem {
                    Label("AI", systemImage: "sparkles")
                }
        }
    }
}
