"""Clientes — cadastro e gestão."""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.models import SessionLocal, Cliente
from dashboard.components import page_header, client_row, empty_state


def render(cliente):
    st.markdown(page_header("⚙️", "Clientes", "Gerencie os clientes da agência"),
                unsafe_allow_html=True)

    tab_lista, tab_novo = st.tabs(["Clientes cadastrados", "Novo cliente"])

    with tab_lista:
        db = SessionLocal()
        try:
            clientes = db.query(Cliente).order_by(Cliente.nome).all()
        finally:
            db.close()

        if not clientes:
            st.markdown(empty_state("👤", "Nenhum cliente ainda",
                                    "Cadastre o primeiro cliente na aba ao lado."),
                        unsafe_allow_html=True)
        else:
            for c in clientes:
                st.markdown(
                    client_row(
                        c.nome, c.segmento or "—", c.cidade or "—",
                        c.telefone or "", c.email or "",
                        selected=(c.id == cliente.id),
                    ),
                    unsafe_allow_html=True,
                )

    with tab_novo:
        with st.form("form_novo_cliente"):
            col1, col2 = st.columns(2)
            nome     = col1.text_input("Nome da empresa *")
            segmento = col2.text_input("Segmento *", placeholder="desentupidora, gasista, chaveiro...")

            col3, col4 = st.columns(2)
            cidade   = col3.text_input("Cidade")
            telefone = col4.text_input("Telefone")

            email = st.text_input("E-mail")
            prompt = st.text_area(
                "Personalidade do atendente virtual",
                value="simpático, profissional, direto ao ponto e ágil",
                height=80,
            )
            salvar = st.form_submit_button("Cadastrar cliente", type="primary",
                                           use_container_width=True)

        if salvar:
            if not nome or not segmento:
                st.warning("Nome e segmento são obrigatórios.")
            else:
                db = SessionLocal()
                try:
                    novo = Cliente(nome=nome, segmento=segmento, cidade=cidade,
                                   telefone=telefone, email=email,
                                   prompt_personalizado=prompt)
                    db.add(novo)
                    db.commit()
                    st.success(f"Cliente '{nome}' cadastrado com sucesso.")
                    st.session_state.pop("cliente_idx", None)
                    st.rerun()
                finally:
                    db.close()
