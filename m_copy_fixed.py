import streamlit as st
import requests
import numpy as np
import random
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

categories = [
    "technology",
    "sports",
    "business",
    "politics",
    "entertainment",
    "health",
    "science",
    "world"
]
n = len(categories)

# -------------------------------
# SESSION STATE
# -------------------------------
if "counts" not in st.session_state:
    st.session_state.counts = np.zeros(n)

if "q_values" not in st.session_state:
    st.session_state.q_values = np.zeros(n)

if "history" not in st.session_state:
    st.session_state.history = []

if "manual_history" not in st.session_state:
    st.session_state.manual_history = []

if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

if "last_manual" not in st.session_state:
    st.session_state.last_manual = None

if "active_category" not in st.session_state:
    st.session_state.active_category = None

if "manual_select" not in st.session_state:
    st.session_state.manual_select = "None"

epsilon = 0.6

# -------------------------------
# RL FUNCTIONS
# -------------------------------
def select_category():
    if np.sum(st.session_state.counts) == 0:
        return random.randint(0, n - 1)

    if random.random() < epsilon:
        return random.randint(0, n - 1)

    return int(np.argmax(st.session_state.q_values))


def update(category_idx, reward):
    st.session_state.counts[category_idx] += 1
    c = st.session_state.counts[category_idx]
    v = st.session_state.q_values[category_idx]
    st.session_state.q_values[category_idx] += (reward - v) / c


# -------------------------------
# CATEGORY DETECTION
# -------------------------------
def detect_category(title):
    title = title.lower()

    if any(word in title for word in ["tech", "ai", "software", "google", "apple"]):
        return "technology"
    elif any(word in title for word in ["cricket", "football", "sports", "match"]):
        return "sports"
    elif any(word in title for word in ["stock", "market", "business", "economy", "bank"]):
        return "business"
    elif any(word in title for word in ["election", "government", "minister", "politics"]):
        return "politics"
    elif any(word in title for word in ["movie", "film", "actor", "celebrity", "bollywood"]):
        return "entertainment"
    elif any(word in title for word in ["health", "hospital", "disease", "covid", "medicine"]):
        return "health"
    elif any(word in title for word in ["science", "research", "space", "nasa"]):
        return "science"
    elif any(word in title for word in ["war", "global", "international", "country"]):
        return "world"
    else:
        return random.choice(categories)


# -------------------------------
# FETCH NEWS (SINGLE CATEGORY)
# -------------------------------
def fetch_news(category):
    page = (st.session_state.refresh_count % 10) + 1

    url = f"https://newsapi.org/v2/everything?q={category}&pageSize=10&page={page}&language=en&sortBy=publishedAt&apiKey={API_KEY}"
    
    res = requests.get(url)
    data = res.json()

    if data.get("status") != "ok":
        return []

    articles = data.get("articles", [])

    for article in articles:
        title = article.get("title", "")
        article["category"] = detect_category(title)

    return articles


# -------------------------------
# FETCH MIXED NEWS 🔥
# -------------------------------
def fetch_mixed_news():
    all_articles = []

    random_categories = random.sample(categories, 3)

    for cat in random_categories:
        articles = fetch_news(cat)
        all_articles.extend(articles[:3])

    random.shuffle(all_articles)
    return all_articles


# -------------------------------
# UI
# -------------------------------
st.title("📰 Smart News Recommendation System")
st.write("👉 Click 👍 on news you like. System will learn your interests!")

# -------------------------------
# MANUAL CATEGORY
# -------------------------------
st.write("### 🎯 Select Category (Optional)")

selected_manual = st.selectbox(
    "Choose category:",
    ["None"] + categories,
    key="manual_select"
)

if selected_manual != "None":
    st.session_state.active_category = selected_manual

    if selected_manual != st.session_state.last_manual:
        st.session_state.manual_history.append(selected_manual)
        st.session_state.last_manual = selected_manual

# -------------------------------
# REFRESH BUTTON
# -------------------------------
if st.button("🔄 Refresh News"):
    st.session_state.refresh_count += 1
    st.session_state.active_category = None
    st.session_state.manual_select = "None"
    st.rerun()

# -------------------------------
# CATEGORY LOGIC
# -------------------------------
if st.session_state.active_category:
    selected_category = st.session_state.active_category
    st.subheader(f"📌 Category Mode: {selected_category.upper()}")

    all_articles = fetch_news(selected_category)
    articles = [a for a in all_articles if a["category"] == selected_category][:5]

else:
    st.subheader("📌 Recommended Feed (Mixed)")

    articles = fetch_mixed_news()[:5]

# fallback
if not articles:
    st.warning("⚠ Showing sample news")
    articles = [
        {"title": "AI is transforming the world", "url": "#", "category": "technology"},
        {"title": "India wins cricket match", "url": "#", "category": "sports"},
        {"title": "Stock market rises today", "url": "#", "category": "business"}
    ]

# -------------------------------
# DISPLAY ARTICLES
# -------------------------------
for i, article in enumerate(articles):
    st.write(f"### {article.get('title', 'No Title')}")
    st.write(f"**Category:** {article.get('category', 'unknown')}")

    if article.get("url"):
        st.write(f"[Read full article]({article['url']})")

    col1, col2 = st.columns(2)

    article_category = article.get("category", "technology")
    category_idx = categories.index(article_category)

    with col1:
        if st.button("👍 Like", key=f"like_{i}_{st.session_state.refresh_count}"):
            update(category_idx, 1)
            st.session_state.history.append(article_category)
            st.success("Preference updated!")

    with col2:
        if st.button("👎 Skip", key=f"skip_{i}_{st.session_state.refresh_count}"):
            update(category_idx, 0)

# -------------------------------
# LEARNING STATUS
# -------------------------------
st.write("---")
st.subheader("📊 Learning Status")

for i in range(n):
    st.write(
        f"{categories[i]} -> score: {st.session_state.q_values[i]:.2f}, "
        f"chosen: {int(st.session_state.counts[i])} times"
    )

# -------------------------------
# HISTORY
# -------------------------------
st.write("---")
st.subheader("🧠 RL Interaction History")
st.write(st.session_state.history)

st.write("---")
st.subheader("🧾 Manual Category Selection History")
st.write(st.session_state.manual_history)