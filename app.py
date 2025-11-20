from dash import Dash, html, dcc, Output, Input
import plotly.express as px
import pandas as pd

df = pd.read_csv("data/olympics_dataset.csv")

df = df[(df["Team"] == "Brazil") & (df["Season"] == "Summer")]
df_medals = df[df["Medal"].isin(["Gold", "Silver", "Bronze"])]
df_medals_unique = df_medals.drop_duplicates(subset=["Year", "Sport", "Event", "Medal"])

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Brasil nas Olimpíadas — Dashboard Interativo"),

    # Dropdown: selecionar esporte
    dcc.Dropdown(
        id="sport_filter",
        options=[{"label": s, "value": s} for s in sorted(df["Sport"].unique())],
        placeholder="Selecione um esporte (opcional)"
    ),

    dcc.Graph(id="medals_by_year"),
    dcc.Graph(id="medals_by_sport"),
    dcc.Graph(id="medals_by_sex"),
    dcc.Graph(id="top_athletes")
])

@app.callback(
    Output("medals_by_year", "figure"),
    Input("sport_filter", "value")
)
def update_medals_year(sport):
    filtered = df_medals_unique.copy()
    if sport:
        filtered = filtered[filtered["Sport"] == sport]

    medals_year = filtered.groupby("Year")["Medal"].count().reset_index()
    fig = px.line(medals_year, x="Year", y="Medal",
                  title="Evolução das Medalhas por Ano")
    return fig


@app.callback(
    Output("medals_by_sport", "figure"),
    Input("sport_filter", "value")
)
def update_medals_sport(sport):
    filtered = df_medals_unique.copy()
    if sport:
        filtered = filtered[filtered["Sport"] == sport]

    medals_sport = filtered.groupby("Sport")["Medal"].count().reset_index()
    fig = px.bar(medals_sport, x="Sport", y="Medal",
                 title="Medalhas por Esporte")
    return fig


@app.callback(
    Output("medals_by_sex", "figure"),
    Input("sport_filter", "value")
)
def update_medals_sex(sport):
    filtered = df_medals_unique.copy()
    if sport:
        filtered = filtered[filtered["Sport"] == sport]

    sex_medals = filtered.groupby("Sex")["Medal"].count().reset_index()
    fig = px.bar(sex_medals, x="Sex", y="Medal",
                 title="Medalhas por Sexo")
    return fig


@app.callback(
    Output("top_athletes", "figure"),
    Input("sport_filter", "value")
)
def update_top_athletes(sport):
    filtered = df_medals_unique.copy()
    if sport:
        filtered = filtered[filtered["Sport"] == sport]

    top = (
        filtered.groupby("Name")["Medal"]
        .count()
        .reset_index()
        .sort_values("Medal", ascending=False)
        .head(10)
    )

    fig = px.bar(top, x="Name", y="Medal",
                 title="Top 10 Atletas Brasileiros por Medalhas")
    return fig

if __name__ == '__main__':
    app.run(debug=True)