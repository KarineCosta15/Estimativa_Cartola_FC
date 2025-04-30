import streamlit as st
import requests
import pandas as pd

# Mapeamentos
posicoes = {
    1: "Goleiro", 2: "Lateral", 3: "Zagueiro", 4: "Meia", 5: "Atacante", 6: "Técnico"
}

status_jogador = {
    1: "Provável",
    2: "Dúvida",
    3: "Suspenso",
    5: "Nulo",
    6: "Poupado",
    7: "Contundido"
}

def obter_dados_rodada():
    url = "https://api.cartola.globo.com/atletas/mercado"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Erro ao acessar dados dos atletas")
        return None

def obter_partidas():
    url = "https://api.cartola.globo.com/partidas"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Erro ao acessar dados das partidas")
        return None

def tratar_dados(dados_rodada, dados_partidas):
    atletas = pd.DataFrame(dados_rodada['atletas'])
    clubes = dados_rodada['clubes']
    partidas = dados_partidas['partidas']

    atletas['posicao'] = atletas['posicao_id'].map(posicoes)
    atletas['status'] = atletas['status_id'].map(status_jogador).fillna("Indefinido")
    atletas['nota_previsao'] = atletas['media_num'] * 0.7 + atletas['pontos_num'] * 0.3

    partidas_df = pd.DataFrame(partidas)
    mando = {}
    for _, row in partidas_df.iterrows():
        mando[row['clube_casa_id']] = ('Casa', row['clube_visitante_id'])
        mando[row['clube_visitante_id']] = ('Fora', row['clube_casa_id'])

    atletas['mando'], atletas['adversario_id'] = zip(*atletas['clube_id'].map(mando))
    atletas['adversario_nome'] = atletas['adversario_id'].map(lambda x: clubes[str(x)]['nome'] if str(x) in clubes else "Desconhecido")
    atletas['clube_nome'] = atletas['clube_id'].map(lambda x: clubes[str(x)]['nome'] if str(x) in clubes else "Desconhecido")

    return atletas

# Interface
st.title("📊 Jogadores por Posição (Dados do Cartola)")
dados_rodada = obter_dados_rodada()
dados_partidas = obter_partidas()

if dados_rodada and dados_partidas:
    rodada_atual = dados_rodada.get("rodada_atual", "Desconhecida")
    st.markdown("### Rodada Atual: **{}**".format(rodada_atual))

    df_jogadores = tratar_dados(dados_rodada, dados_partidas)

    if df_jogadores['status'].nunique() == 1 and df_jogadores['status'].iloc[0] == "Indefinido":
        st.warning("⚠️ Os status dos jogadores ainda não foram atualizados.")

    for pos in posicoes.values():
        st.subheader(f"📌 {pos}")
        df_pos = df_jogadores[df_jogadores['posicao'] == pos].copy()
        df_pos = df_pos.sort_values(by='nota_previsao', ascending=False)
        if df_pos.empty:
            st.info(f"Nenhum jogador encontrado para {pos}.")
        else:
            st.dataframe(df_pos[[
                'apelido', 'clube_nome', 'status', 'mando', 'adversario_nome',
                'preco_num', 'nota_previsao'
            ]].rename(columns={
                'apelido': 'Nome',
                'clube_nome': 'Time',
                'status': 'Status',
                'mando': 'Mando',
                'adversario_nome': 'Adversário',
                'preco_num': 'Cartoletas',
                'nota_previsao': 'Pontuação Esperada'
            }))
