import os
import random
from typing import List, Dict

import numpy as np
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

CATEGORIES = [
    "technology",
    "sports",
    "business",
    "politics",
    "entertainment",
    "health",
    "science",
    "world",
]

EPSILON = 0.25
PAGE_SIZE = 8
FALLBACK_ARTICLES = [
    {
        "title": "AI tools continue to reshape software teams",
        "url": "#",
        "source_name": "Demo Feed",
        "description": "Technology headlines used when the API is unavailable.",
        "category": "technology",
    },
    {
        "title": "Championship clash keeps fans on edge",
        "url": "#",
        "source_name": "Demo Feed",
        "description": "Sports headlines used when the API is unavailable.",
        "category": "sports",
    },
    {
        "title": "Markets react to fresh economic signals",
        "url": "#",
        "source_name": "Demo Feed",
        "description": "Business headlines used when the API is unavailable.",
        "category": "business",
    },
]


def init_state() -> None:
    n = len(CATEGORIES)
    if "counts" not in st.session_state:
        st.session_state.counts = np.zeros(n)
    if "q_values" not in st.session_state:
        st.session_state.q_values = np.zeros(n)
    if "feedback_log" not in st.session_state:
        st.session_state.feedback_log = []
    if "manual_history" not in st.session_state:
        st.session_state.manual_history = []
    if "manual_category" not in st.session_state:
        st.session_state.manual_category = None
    if "page_by_category" not in st.session_state:
        st.session_state.page_by_category = {category: 1 for category in CATEGORIES}
    if "last_selected_category" not in st.session_state:
        st.session_state.last_selected_category = None


def category_keywords() -> Dict[str, List[str]]:
    return {
        "technology": ["tech", "ai", "software", "google", "apple", "startup", "chip"],
        "sports": ["cricket", "football", "sports", "match", "league", "tournament"],
        "business": ["stock", "market", "business", "economy", "bank", "trade", "finance"],
        "politics": ["election", "government", "minister", "politics", "policy", "senate"],
        "entertainment": ["movie", "film", "actor", "celebrity", "music", "bollywood"],
        "health": ["health", "hospital", "disease", "covid", "medicine", "wellness"],
        "science": ["science", "research", "space", "nasa", "climate", "study"],
        "world": ["war", "global", "international", "country", "diplomatic", "conflict"],
    }


def detect_category(title: str, description: str = "") -> str:
    content = f"{title} {description}".lower()
    for category, keywords in category_keywords().items():
        if any(keyword in content for keyword in keywords):
            return category
    return random.choice(CATEGORIES)


def choose_category() -> str:
    manual_category = st.session_state.manual_category
    if manual_category:
        return manual_category

    if np.sum(st.session_state.counts) == 0:
        return random.choice(CATEGORIES)

    if random.random() < EPSILON:
        return random.choice(CATEGORIES)

    best_idx = int(np.argmax(st.session_state.q_values))
    return CATEGORIES[best_idx]


def update_preferences(category: str, reward: float) -> None:
    idx = CATEGORIES.index(category)
    st.session_state.counts[idx] += 1
    count = st.session_state.counts[idx]
    current_value = st.session_state.q_values[idx]
    st.session_state.q_values[idx] += (reward - current_value) / count


def fetch_news(category: str) -> List[dict]:
    if not API_KEY:
        return []

    page = st.session_state.page_by_category.get(category, 1)
    url = (
        "https://newsapi.org/v2/everything"
        f"?q={category}&pageSize={PAGE_SIZE}&page={page}&language=en"
        f"&sortBy=publishedAt&apiKey={API_KEY}"
    )

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return []

    if payload.get("status") != "ok":
        return []

    articles = payload.get("articles", [])
    cleaned_articles = []

    for article in articles:
        title = article.get("title") or "No Title"
        description = article.get("description") or ""
        cleaned_articles.append(
            {
                "title": title,
                "description": description,
                "url": article.get("url") or "#",
                "source_name": (article.get("source") or {}).get("name", "Unknown"),
                "category": detect_category(title, description),
                "queried_category": category,
            }
        )

    return cleaned_articles


def next_page(category: str) -> None:
    st.session_state.page_by_category[category] = st.session_state.page_by_category.get(category, 1) + 1


def reset_learning() -> None:
    n = len(CATEGORIES)
    st.session_state.counts = np.zeros(n)
    st.session_state.q_values = np.zeros(n)
    st.session_state.feedback_log = []
    st.session_state.manual_history = []
    st.session_state.manual_category = None
    st.session_state.page_by_category = {category: 1 for category in CATEGORIES}
    st.session_state.last_selected_category = None


init_state()

st.set_page_config(page_title="News Recommendation with RL", layout="wide")
st.title("News Recommendation System Using Reinforcement Learning")
st.write("This app learns your preferred news categories from your Like and Skip feedback.")

with st.sidebar:
    st.header("Controls")

    selected_manual = st.selectbox(
        "Manual category",
        ["None"] + CATEGORIES,
        index=(["None"] + CATEGORIES).index(
            st.session_state.manual_category if st.session_state.manual_category in CATEGORIES else "None"
        ),
    )

    if st.button("Apply Category", use_container_width=True):
        if selected_manual == "None":
            st.session_state.manual_category = None
        else:
            st.session_state.manual_category = selected_manual
            if not st.session_state.manual_history or st.session_state.manual_history[-1] != selected_manual:
                st.session_state.manual_history.append(selected_manual)
        st.rerun()

    if st.button("Refresh Articles", use_container_width=True):
        active_category = st.session_state.last_selected_category or choose_category()
        next_page(active_category)
        st.rerun()

    if st.button("Reset Learning", use_container_width=True):
        reset_learning()
        st.rerun()

selected_category = choose_category()
st.session_state.last_selected_category = selected_category

mode_label = "Manual category mode" if st.session_state.manual_category else "RL recommended mode"
st.subheader(f"{mode_label}: {selected_category.upper()}")

articles = fetch_news(selected_category)
if not articles:
    articles = [article for article in FALLBACK_ARTICLES if article["category"] == selected_category]
if not articles:
    articles = FALLBACK_ARTICLES

for index, article in enumerate(articles[:5]):
    st.markdown(f"### {article['title']}")
    st.write(f"Source: {article['source_name']}")
    st.write(f"Detected category: {article['category']}")
    if article.get("description"):
        st.write(article["description"])
    if article.get("url"):
        st.markdown(f"[Read full article]({article['url']})")

    like_col, skip_col = st.columns(2)

    with like_col:
        if st.button("Like", key=f"like_{selected_category}_{index}"):
            reward_category = article.get("category", selected_category)
            update_preferences(reward_category, 1.0)
            st.session_state.feedback_log.append(
                {"article": article["title"], "category": reward_category, "reward": 1}
            )
            st.rerun()

    with skip_col:
        if st.button("Skip", key=f"skip_{selected_category}_{index}"):
            reward_category = article.get("category", selected_category)
            update_preferences(reward_category, 0.0)
            st.session_state.feedback_log.append(
                {"article": article["title"], "category": reward_category, "reward": 0}
            )
            st.rerun()

    st.write("---")

st.subheader("Learning Status")
for idx, category in enumerate(CATEGORIES):
    st.write(
        f"{category}: score={st.session_state.q_values[idx]:.2f}, "
        f"feedback_count={int(st.session_state.counts[idx])}"
    )

st.subheader("Feedback History")
st.write(st.session_state.feedback_log if st.session_state.feedback_log else "No feedback yet.")

st.subheader("Manual Category History")
st.write(st.session_state.manual_history if st.session_state.manual_history else "No manual categories applied yet.")
