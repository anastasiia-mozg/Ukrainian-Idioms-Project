import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
from collections import defaultdict

from idiom_exctractor_backend import IdiomExtractorAppService
from idiom_llm_extractor import RateLimitExceeded


# ========== App Navigation State ==========

if "page" not in st.session_state:
    st.session_state.page = "intro"

def go_to_input():
    st.session_state.page = "input"

def restart():
    st.session_state.page = "intro"


# ========== Highlight Function ==========

def highlight_text(text, dict_idioms, model_idioms, shared_idioms):
    shared = set(i.lower() for i in shared_idioms)
    dict_only = set(i.lower() for i in dict_idioms) - shared
    model_only = set(i.lower() for i in model_idioms) - shared

    colors = {
        "shared": "#a8e6cf",
        "dict":   "#ffd3b6",
        "model":  "#a0c4ff",
    }

    all_idioms = (
        [(i, "shared") for i in shared] +
        [(i, "dict") for i in dict_only] +
        [(i, "model") for i in model_only]
    )
    all_idioms.sort(key=lambda x: len(x[0]), reverse=True)

    for idiom, source in all_idioms:
        pattern = re.compile(re.escape(idiom), re.IGNORECASE)
        color = colors[source]
        text = pattern.sub(
            lambda m: f'<span style="background-color:{color};padding:2px 4px;border-radius:3px;">{m.group()}</span>',
            text
        )
    return text


# ========== Page: Intro ==========

if st.session_state.page == "intro":
    st.title("✨ Idiom Extractor")
    st.subheader("Ласкаво просимо до Idiom Extractor!")

    st.markdown("""
    За допомогою нашого застосунку ви можете видобути фразеологізми з будь-якого тексту, використовуючи два методи:
    """)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""- **Метод 1:** Словниковий пошук  
Цей метод використовує набір фразеологізмів із СУМ та виявляє їх у тексті разом з їх варіаціями.""")
    with col2:
        st.markdown("""- **Метод 2:** Модель (Gemini)  
Модель знаходить у тексті фразеологізми без використання словників, завдяки глибокому розумінню мови.""")

    st.markdown("⭐ Введіть свій текст — і отримайте результат у вигляді списку ідіом зі статистикою.")
    st.button("Почати", on_click=go_to_input)

    st.markdown("""
    <div style='position: fixed; bottom: 10px; width: 100%; text-align: center; color: gray; font-size: 0.9em;'>
        ©2025 Розробниці: Мозгова Анастасія та Карпцова Юліана
    </div>
    """, unsafe_allow_html=True)


# ========== Page: Input ==========

elif st.session_state.page == "input":
    st.title("📝 Обробити текст")
    st.markdown("Введіть текст для аналізу:")
    text = st.text_area("", placeholder="Напишіть речення", height=300)

    if st.button("Обробити"):
        st.session_state.text = text
        st.session_state.ready = False
        st.session_state.page = "results"
        st.rerun()

    if st.button("Назад"):
        st.session_state.page = "intro"
        st.rerun()


# ========== Page: Results ==========

elif st.session_state.page == "results":
    st.title("📊 Результати")

    if "ready" not in st.session_state or not st.session_state.ready:
        with st.spinner("⏳ Обробка тексту..."):
            try:
                extractor_service = IdiomExtractorAppService()
                results = extractor_service.extract_idioms(st.session_state.text)

                st.session_state.dict_idioms = results["dict_idioms"]
                st.session_state.model_idioms = results["model_idioms"]
                st.session_state.shared_idioms = results["shared_idioms"]
                st.session_state.idioms_stats = results["idioms_stats"]
                st.session_state.original_text = results["original_text"]
                st.session_state.ready = True

            except RateLimitExceeded as e:
                st.error(str(e))
                st.button("⬅️ Повернутись", on_click=go_to_input)
                st.stop()

    # ==== HIGHLIGHTED TEXT ====
    st.markdown("### 🔍 Текст з виділеними фразеологізмами")
    st.markdown("""
        <span style='background:#a8e6cf;padding:2px 6px;border-radius:3px;'>█</span> Обидва методи &nbsp;&nbsp;
        <span style='background:#ffd3b6;padding:2px 6px;border-radius:3px;'>█</span> Словник &nbsp;&nbsp;
        <span style='background:#a0c4ff;padding:2px 6px;border-radius:3px;'>█</span> Модель
    """, unsafe_allow_html=True)

    highlighted = highlight_text(
        st.session_state.original_text,
        st.session_state.dict_idioms,
        st.session_state.model_idioms,
        st.session_state.shared_idioms
    )
    st.markdown(f"<div style='line-height:2;font-size:1.1em;margin-top:10px;'>{highlighted}</div>",
                unsafe_allow_html=True)

    st.markdown("---")

    # ==== BAR CHART ====
    method_names = ["Модель", "Словник"]
    counts = [len(st.session_state.model_idioms), len(st.session_state.dict_idioms)]

    fig = go.Figure(data=[
        go.Bar(name='Фразеологізми', x=method_names, y=counts, marker_color=['royalblue', 'coral'])
    ])
    fig.update_layout(title="Кількість знайдених фразеологізмів за методом")
    st.plotly_chart(fig, use_container_width=True)

    # ==== DOWNLOAD BUTTONS ====
    model_df = pd.DataFrame(st.session_state.model_idioms, columns=["Model Idioms"])
    dict_df = pd.DataFrame(st.session_state.dict_idioms, columns=["Dictionary Idioms"])

    col1, col2 = st.columns([1, 1])
    with col1:
        st.download_button("⬇️ Завантажити фразеологізми (модель)",
                           model_df.to_csv(index=False, encoding='utf-8-sig'),
                           file_name="model_idioms.csv", mime="text/csv")
    with col2:
        st.download_button("⬇️ Завантажити фразеологізми (словник)",
                           dict_df.to_csv(index=False, encoding='utf-8-sig'),
                           file_name="dict_idioms.csv", mime="text/csv")

    # ==== SHARED IDIOMS ====
    with st.expander("📊 Спільні фразеологізми"):
        if len(st.session_state.shared_idioms) != 0:
            st.write("**Спільні фразеологізми:**")
            for idiom in st.session_state.shared_idioms:
                st.write(f"- {idiom}")
        else:
            st.write("**Спільних фразеологізмів немає:(**")

    st.button("Почати заново", on_click=go_to_input)
