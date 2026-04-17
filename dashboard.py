
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuration de la page (sans icône)
st.set_page_config(
    page_title="Prix des Matières Premières",
    layout="wide"
)

# Style personnalisé (couleurs, polices)
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fa;
    }
    .css-18e3th9 {
        padding-top: 1rem;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1e3a5f;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #4a627a;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        text-align: center;
        border-left: 4px solid #1e3a5f;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #6b7c93;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Titre
st.markdown('<div class="main-title">📈 Prix des Matières Premières</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Suivi historique des prix | Or, Argent, Pétrole, Cacao, Café, Blé, Cuivre, Gaz Naturel</div>', unsafe_allow_html=True)

# Chargement des données
@st.cache_data
def load_data():
    try:
        response = requests.get("http://localhost:5000/data?limit=10000", timeout=10)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data["data"])
            df["date"] = pd.to_datetime(df["date"])
            return df
        else:
            st.error(f"Erreur API: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Impossible de contacter l'API: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Aucune donnée chargée. Vérifiez que l'API est démarrée.")
    st.stop()

# Filtres latéraux
st.sidebar.markdown("### Filtres")

# Sélection des matières
matieres_list = sorted(df["matiere"].unique())
selected_matieres = st.sidebar.multiselect(
    "Matières",
    matieres_list,
    default=["gold", "silver", "copper", "crude_oil", "natural_gas", "cocoa", "coffee"]
)

# Sélection des années
annees_list = sorted(df["annee"].unique(), reverse=True)
selected_annees = st.sidebar.multiselect(
    "Années",
    annees_list,
    default=annees_list[:5]
)

# Application des filtres
mask = pd.Series([True] * len(df))
if selected_matieres:
    mask &= df["matiere"].isin(selected_matieres)
if selected_annees:
    mask &= df["annee"].isin(selected_annees)

df_filtered = df[mask]

# Métriques principales (en haut)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{len(df_filtered):,}</div>
        <div class="metric-label">Observations</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{df_filtered["matiere"].nunique()}</div>
        <div class="metric-label">Matières suivies</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{df_filtered["categorie"].nunique()}</div>
        <div class="metric-label">Catégories</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{df_filtered["annee"].min()} - {df_filtered["annee"].max()}</div>
        <div class="metric-label">Période</div>
    </div>
    """, unsafe_allow_html=True)

# Graphique 1: Évolution des prix (courbes)
st.markdown("### Évolution des prix par matière")

fig1 = px.line(
    df_filtered,
    x="date",
    y="prix",
    color="matiere",
    title="",
    labels={"prix": "Prix (USD)", "date": "Date", "matiere": "Matière"},
    color_discrete_sequence=px.colors.qualitative.Set2
)

fig1.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)
fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#e6e9ef")
fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#e6e9ef")

st.plotly_chart(fig1, use_container_width=True)

# Graphique 2: Comparaison des prix (barres groupées - dernière année)
st.markdown("### Prix moyens par matière (dernière année disponible)")

derniere_annee = df_filtered["annee"].max()
df_last_year = df_filtered[df_filtered["annee"] == derniere_annee]
prix_moyens = df_last_year.groupby("matiere")["prix"].mean().reset_index()
prix_moyens = prix_moyens.sort_values("prix", ascending=False)

fig2 = px.bar(
    prix_moyens,
    x="matiere",
    y="prix",
    title=f"Prix moyen par matière en {derniere_annee}",
    labels={"prix": "Prix (USD)", "matiere": ""},
    color="prix",
    color_continuous_scale="Blues",
    text_auto=".2f"
)

fig2.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    height=450,
    showlegend=False
)
fig2.update_xaxes(tickangle=45)
fig2.update_traces(textposition="outside")

st.plotly_chart(fig2, use_container_width=True)

# Graphique 3: Heatmap des corrélations
st.markdown("### Corrélation entre les prix des matières")

df_pivot = df_filtered.pivot_table(index="date", columns="matiere", values="prix").dropna()
corr_matrix = df_pivot.corr()

fig3 = px.imshow(
    corr_matrix,
    text_auto=True,
    aspect="auto",
    color_continuous_scale="RdBu_r",
    title="Matrice de corrélation",
    labels={"color": "Corrélation", "x": "", "y": ""}
)

fig3.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    height=600,
    xaxis=dict(tickangle=45)
)

st.plotly_chart(fig3, use_container_width=True)

# Tableau des données (optionnel, déroulé)
with st.expander("📋 Voir les données détaillées"):
    st.dataframe(
        df_filtered[["date", "matiere", "categorie", "prix", "unite", "source"]].sort_values("date", ascending=False),
        use_container_width=True,
        hide_index=True
    )

# Pied de page
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #8898aa; font-size: 0.8rem;'>"
    "Données historiques des prix des matières premières | Source: Macrotrends | API développée avec Flask"
    "</div>",
    unsafe_allow_html=True
)