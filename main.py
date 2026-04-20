import os
import random

import numpy as np
import requests
import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="Smart News Recommendation", page_icon="🗞️", layout="wide")

load_dotenv()
API_KEY = os.getenv("API_KEY") or st.secrets.get("API_KEY", "")

# -------------------------------
# 🎨 UI STYLING
# -------------------------------
st.markdown("""
<style>
.main {background-color: #f8fafc;}

.card {
    background: linear-gradient(135deg, #ffffff, #f1f5f9);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.title {
    font-size: 20px;
    font-weight: bold;
    color: #1e293b;
}

.category {
    display:inline-block;
    padding:6px 12px;
    border-radius:12px;
    font-size:13px;
    margin-bottom:10px;
}

/* Category Colors */
.technology {background:#dbeafe;color:#1d4ed8;}
.sports {background:#dcfce7;color:#15803d;}
.business {background:#fef3c7;color:#b45309;}
.politics {background:#fee2e2;color:#b91c1c;}
.entertainment {background:#f3e8ff;color:#7c3aed;}
.health {background:#ecfeff;color:#0e7490;}
.science {background:#e0f2fe;color:#0369a1;}
.world {background:#f1f5f9;color:#334155;}

.link a {
    color:#2563eb;
    text-decoration:none;
    font-weight:500;
}
.link a:hover {text-decoration:underline;}

.stButton>button {
    border-radius:10px;
    padding:8px 15px;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# CATEGORIES
# -------------------------------
categories = [
    "technology", "sports", "business", "politics",
    "entertainment", "health", "science", "world"
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

if "refresh_count" not in st.session_state:
    st.session_state.refresh_count = 0

if "selected_learning" not in st.session_state:
    st.session_state.selected_learning = None

epsilon = 0.6

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.title("⚙️ Filters")

mode = st.sidebar.radio("Select Mode:", ["Mixed Feed", "Category Filter"])
selected_sidebar_category = st.sidebar.selectbox("Select Category:", categories)

if st.sidebar.button("🔄 Refresh News"):
    st.session_state.refresh_count += 1
    st.rerun()

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
# CATEGORY DETECTION (for filtering only)
# -------------------------------
def detect_category(title):
    title = title.lower()

    if any(w in title for w in ["ai","technology","tech","software","app","startup"]):
        return "technology"
    elif any(w in title for w in ["cricket","football","match","ipl"]):
        return "sports"
    elif any(w in title for w in ["election","government","minister"]):
        return "politics"
    elif any(w in title for w in ["movie","film","actor","celebrity"]):
        return "entertainment"
    elif any(w in title for w in ["health","disease","medicine"]):
        return "health"
    elif any(w in title for w in ["science","space","nasa"]):
        return "science"
    elif any(w in title for w in ["stock","market","economy","finance"]):
        return "business"
    else:
        return "world"

# -------------------------------
# FETCH NEWS
# -------------------------------
def fetch_news(selected_category, is_manual):
    page = (st.session_state.refresh_count % 5) + 1

    if not is_manual:
        query = "india OR technology OR sports OR business OR politics OR entertainment"
    else:
        query_map = {
            "technology": "technology OR AI",
            "sports": "sports OR cricket",
            "business": "business OR stock market",
            "politics": "politics OR government",
            "entertainment": "movies OR celebrities",
            "health": "health OR medicine",
            "science": "science OR space",
            "world": "world news"
        }
        query = query_map.get(selected_category, selected_category)

    url = f"https://newsapi.org/v2/everything?q={query}&pageSize=10&page={page}&language=en&sortBy=publishedAt&apiKey={API_KEY}"

    res = requests.get(url)
    data = res.json()

    if data.get("status") != "ok":
        return []

    articles = data.get("articles", [])

    for article in articles:
        article["category"] = detect_category(article.get("title", ""))

    return articles

# -------------------------------
# HEADER
# -------------------------------
st.markdown("<h1 style='text-align:center;'>📰 Smart News Recommendation</h1>", unsafe_allow_html=True)

# -------------------------------
# CATEGORY LOGIC
# -------------------------------
if mode == "Category Filter":
    is_manual = True
    selected_category = selected_sidebar_category
    st.subheader(f"📌 Category: {selected_category.upper()}")
else:
    is_manual = False
    cat_idx = select_category()
    selected_category = categories[cat_idx]
    st.subheader(f"📌 RL-Based Category: {selected_category.upper()}")

# -------------------------------
# FETCH DATA
# -------------------------------
all_articles = fetch_news(selected_category, is_manual)

# -------------------------------
# DISPLAY LOGIC
# -------------------------------
if is_manual:
    articles = [a for a in all_articles if a["category"] == selected_category][:5]
else:
    preferred = [a for a in all_articles if a["category"] == selected_category]
    others = [a for a in all_articles if a["category"] != selected_category]
    articles = (preferred + others)[:5]

# -------------------------------
# ✅ DISPLAY ARTICLES (FINAL FIX)
# -------------------------------
for i, article in enumerate(articles):

    cat = article.get("category", "world")

    st.markdown(f"""
    <div class="card">
        <div class="category {cat}">{cat.upper()}</div>
        <div class="title">{article.get('title','No Title')}</div>
    </div>
    """, unsafe_allow_html=True)

    if article.get("url"):
        st.markdown(f"<div class='link'>🔗 <a href='{article['url']}' target='_blank'>Read full article</a></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # 🔥 FINAL FIX (NO MORE BUG)
    cat_idx = categories.index(cat)

    with col1:
        if st.button("👍 Like", key=f"like_{i}_{st.session_state.refresh_count}"):
            update(cat_idx, 1)
            st.session_state.history.append(cat)
            st.success(f"Liked: {cat}")

    with col2:
        if st.button("👎 Skip", key=f"skip_{i}_{st.session_state.refresh_count}"):
            update(cat_idx, 0)

    st.markdown("---")

# -------------------------------
# 📊 LEARNING
# -------------------------------
st.subheader("📊 Learning")

cols = st.columns(4)

for i in range(n):
    with cols[i % 4]:
        if st.button(categories[i].upper(), key=f"learn_{i}"):
            st.session_state.selected_learning = i

if st.session_state.selected_learning is not None:
    idx = st.session_state.selected_learning
    st.success(f"Category: {categories[idx].upper()}")
    st.info(f"Score: {st.session_state.q_values[idx]:.2f}")
    st.info(f"Chosen: {int(st.session_state.counts[idx])} times")

# -------------------------------
# HISTORY
# -------------------------------
st.subheader("🧠 Interaction History")
st.write(st.session_state.history)
