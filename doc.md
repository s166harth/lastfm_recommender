# Song Recommendation Scoring Algorithm

The final score for each song is a weighted sum designed to measure not just what you play, but *how* you play it. It balances raw popularity with consistency and overall interest in the artist and album.

Here is a breakdown of the four components that make up the score:

### 1. Frequency Score (Weight: 1.0)
*   **What it is:** The simplest factor. It's the total number of times you played a song in the 5-day period.
*   **Why it matters:** A song you play a lot is clearly a song you like. This is the most direct signal of interest.
*   **Calculation:** `Play Count * 1.0`

### 2. Consistency Score (Weight: 1.5)
*   **What it is:** The number of *unique days* you listened to the song. If you played a song 5 times on Friday, its consistency is 1. If you played it once every day from Monday to Friday, its consistency is 5.
*   **Why it matters:** This is the most heavily weighted factor because it's excellent at identifying your "staples." A song that is part of your routine on multiple days is more likely a long-term favorite than a song you just binged once.
*   **Calculation:** `Number of Unique Days Played * 1.5`

### 3. Artist Affinity Score (Weight: 0.5)
*   **What it is:** The total number of scrobbles for the song's artist across all their songs you played. If you listened to 10 Muse songs and 2 Queen songs, every Muse track gets a boost from an affinity score of 10, and every Queen track gets a boost from an affinity of 2.
*   **Why it matters:** It captures your current interest in an artist. This helps elevate other great songs by an artist you're focused on, even if you only played those specific songs once or twice.
*   **Calculation:** `Total Plays for the Artist * 0.5`

### 4. Album Affinity Score (Weight: 0.3)
*   **What it is:** Similar to Artist Affinity, this is the total number of scrobbles from the song's specific album.
*   **Why it matters:** It identifies tracks from albums you're listening to heavily. If you're working your way through a new album, this ensures its tracks get recommended.
*   **Calculation:** `Total Plays for the Album * 0.3`

---

### Putting It All Together

The final score is the sum of these four parts:

`Final Score = (Frequency * 1.0) + (Consistency * 1.5) + (Artist Affinity * 0.5) + (Album Affinity * 0.3)`

This model ensures that the top recommendations are songs that you not only play frequently but also listen to consistently, and which belong to the artists and albums that are dominating your listening time.
