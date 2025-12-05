from dash import Dash, html, dcc, Output, Input
import plotly.express as px
import pandas as pd
import numpy as np

df = pd.read_csv("data/olympics_dataset.csv")

df = df[(df["Team"] == "Brazil") & (df["Season"] == "Summer")]
df_medals = df[df["Medal"].isin(["Gold", "Silver", "Bronze"])]
df_medals_unique = df_medals.drop_duplicates(subset=["Year", "Sport", "Event", "Medal"])
year_city = df.drop_duplicates(subset=["Year"])[["Year", "City"]]


card_style = {
    "background": "white",
    "padding": "20px",
    "borderRadius": "12px",
    "boxShadow": "0px 0px 10px rgba(0,0,0,0.1)",
    "margin": "10px",
    "flex": "1",
    "minWidth": "400px"
}

row_style = {
    "display": "flex",
    "flexWrap": "wrap",
    "justifyContent": "space-between"
}

app = Dash(__name__)

app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "padding": "20px",
        "maxWidth": "1400px",
        "margin": "0 auto"
    },
    children=[
        html.H1("Brasil nas Olimpíadas — Dashboard Interativo",
                style={"textAlign": "center", "marginBottom": "40px"}),

        html.Div([
            dcc.Dropdown(
                id="sport_filter",
                options=[{"label": s, "value": s} for s in sorted(df["Sport"].unique())],
                placeholder="Selecione um esporte (opcional)",
                style={"width": "50%"}
            )
        ], style={"display": "flex", "justifyContent": "center", "marginBottom": "30px"}),

        html.Div([
            html.Div([dcc.Graph(id="medals_by_year")], style=card_style),
            html.Div([dcc.Graph(id="medals_by_sport")], style=card_style),
        ], style=row_style),

        html.Div([
            html.Div([dcc.Graph(id="medals_by_sex_evolution")], style=card_style),
            html.Div([dcc.Graph(id="top_athletes_sex")], style=card_style),
        ], style=row_style),

        html.Div([
            html.Div([dcc.Graph(id="growth_sports")], style=card_style),
            html.Div([dcc.Graph(id="forecast_medals")], style=card_style),
        ], style=row_style),

        html.Div([
            html.Div([dcc.Graph(id="promising_by_sex")], style=card_style),
        ], style=row_style),
    ]
)

@app.callback(
    Output("medals_by_year", "figure"),
    Input("sport_filter", "value")
)
def update_medals_year(sport):
    filtered = df_medals_unique.copy()
    if sport:
        filtered = filtered[filtered["Sport"] == sport]

    medals_year = filtered.groupby("Year")["Medal"].count().reset_index()

    medals_year = medals_year.merge(year_city, on="Year", how="left")

    fig = px.line(
        medals_year,
        x="Year",
        y="Medal",
        title="Evolução das Medalhas por Ano"
    )

    fig.update_traces(
        hovertemplate="<br>".join([
            "Ano: %{x}",
            "Medalhas: %{y}",
            "Cidade: %{customdata}"
        ]),
        customdata=medals_year["City"]
    )

    return fig

@app.callback(
    Output("medals_by_sport", "figure"),
    Input("sport_filter", "value")
)
def update_medals_sport(sport):
    filtered = df_medals_unique.copy()
    if sport:
        filtered = filtered[filtered["Sport"] == sport]

    medals_sport = (
        filtered.groupby("Sport")["Medal"]
        .count()
        .reset_index()
        .sort_values("Medal", ascending=False)
    )

    fig = px.bar(medals_sport, x="Sport", y="Medal",
                 title="Medalhas por Esporte (Ordenado)")
    return fig

@app.callback(
    Output("medals_by_sex_evolution", "figure"),
    Input("sport_filter", "value")
)
def update_medals_sex_evolution(sport):
    filtered = df_medals_unique.copy()
    if sport:
        filtered = filtered[filtered["Sport"] == sport]

    evolution = (
        filtered.groupby(["Year", "Sex"])["Medal"]
        .count()
        .reset_index()
    )

    evolution = evolution.merge(year_city, on="Year", how="left")

    fig = px.line(
        evolution,
        x="Year",
        y="Medal",
        color="Sex",
        markers=True,
        title="Evolução de Medalhas por Sexo ao Longo dos Anos"
    )

    for sex_value in evolution["Sex"].unique():
        subset = evolution[evolution["Sex"] == sex_value]

        fig.for_each_trace(
            lambda trace: trace.update(
                customdata=subset[["City", "Sex"]].to_numpy(),
                hovertemplate="<br>".join([
                    "Ano: %{x}",
                    "Medalhas: %{y}",
                    "Sexo: %{customdata[1]}",
                    "Cidade: %{customdata[0]}"
                ])
            )
            if trace.name == sex_value else None
        )

    return fig

@app.callback(
    Output("top_athletes_sex", "figure"),
    Input("sport_filter", "value")
)
def update_top_athletes_sex(sport):
    filtered = df_medals_unique.copy()
    if sport:
        filtered = filtered[filtered["Sport"] == sport]

    ranking = (
        filtered.groupby(["Sex", "Name"])["Medal"]
        .count()
        .reset_index()
    )

    ranking_top = (
        ranking.sort_values(["Sex", "Medal"], ascending=[True, False])
        .groupby("Sex")
        .head(10)
    )

    fig = px.bar(
        ranking_top,
        x="Name",
        y="Medal",
        color="Sex",
        title="Top 10 Atletas por Sexo"
    )

    fig.update_layout(xaxis={'categoryorder': 'total descending'})
    return fig

@app.callback(
    Output("growth_sports", "figure"),
    Input("sport_filter", "value")
)
def update_growth_sports(sport):
    filtered = df_medals_unique.copy()

    growth = (
        filtered.groupby(["Sport", "Year"])["Medal"]
        .count()
        .reset_index()
    )

    growth_summary = (
        growth.groupby("Sport")
        .apply(lambda g: (
            g[g["Year"] == g["Year"].max()]["Medal"].values[0]
            - g[g["Year"] == g["Year"].min()]["Medal"].values[0]
        ))
        .reset_index(name="Growth")
        .sort_values("Growth", ascending=False)
        .head(10)
    )

    fig = px.bar(growth_summary, x="Sport", y="Growth",
                 title="Modalidades que Mais Crescem em Medalhas")
    return fig

@app.callback(
    Output("forecast_medals", "figure"),
    Input("sport_filter", "value")
)
def update_forecast(sport):
    filtered = df_medals_unique.copy()

    medals_year = (
        filtered.groupby("Year")["Medal"]
        .count()
        .reset_index()
        .sort_values("Year")
    )

    X = medals_year["Year"]
    y = medals_year["Medal"]

    coef = np.polyfit(X, y, 1)
    poly = np.poly1d(coef)

    future_years = [2028, 2032]
    future_preds = poly(future_years)

    df_future = pd.DataFrame({
        "Year": future_years,
        "Medal": future_preds
    })

    fig = px.line(medals_year, x="Year", y="Medal",
                  title="Projeção de Medalhas Futuras (Regressão Linear)")

    fig.add_scatter(
        x=df_future["Year"],
        y=df_future["Medal"],
        mode="markers+lines",
        name="Previsão"
    )

    return fig

@app.callback(
    Output("promising_by_sex", "figure"),
    Input("sport_filter", "value")
)
def update_promising_by_sex(sport):
    recent_years = df_medals_unique["Year"].max() - 20
    df_recent = df_medals_unique[df_medals_unique["Year"] >= recent_years]

    growth = (
        df_recent.groupby(["Sport", "Sex"])["Medal"]
        .count()
        .reset_index()
    )

    fig = px.bar(
        growth,
        x="Sport",
        y="Medal",
        color="Sex",
        barmode="group",
        title="Modalidades Mais Promissoras por Sexo (Últimos 20 anos)"
    )

    return fig


if __name__ == "__main__":
    app.run(debug=True)
