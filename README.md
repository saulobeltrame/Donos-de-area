# LATAM MRO — Projeto Donos de Área: Líderes

> **Dashboard de Auditoria, Conformidade Operacional e Acompanhamento de Inspeções da Liderança Técnica.**  
> *Base de Manutenção: LATAM MRO — São Carlos (QSC)*

![Python](https://img.shields.io/badge/Python-3.11+-10004F?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-ED1651?style=for-the-badge&logo=streamlit&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-Service_Account-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)
![Status](https://img.shields.io/badge/Status-Produção_Enterprise-10B981?style=for-the-badge)

---

## Visão Geral

O **Projeto Donos de Área** é um programa contínuo de excelência operacional no hangar do **LATAM MRO São Carlos**, voltado à mitigação de riscos, organização 5S e prevenção ativa de FOD nos hangares e aeronaves em manutenção.

Este repositório contempla a **camada gerencial de visualização de dados** de um ecossistema integrado de 3 etapas desenvolvido para o projeto:

```text
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│   1. COLETA EM CAMPO    │      │   2. INGESTÃO & NUVEM   │      │   3. GESTÃO À VISTA     │
│   Líderes de Manutenção │ ───► │  Google Cloud / Sheets  │ ───► │ Coordenação/Supervisão  │
│  (Formulário Dedicado)  │      │                         │      │    (Este Dashboard)     │
│                         │      │                         │      │                         │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```
* **Coleta Operacional:** Os líderes executam as rotinas de inspeção e registram os apontamentos por meio de um formulário (app dedicado).
* **Pipeline de Dados:** Centralização, validação e persistência dos apontamentos em tempo real.
* **Auditoria & Tomada de Decisão (Dashboard):** Coordenadores e supervisores acompanham o cumprimento de metas de cobertura, rastreiam desvios críticos, auditam o rigor dos checklists e passagens de turno.

## Principais Funcionalidades

* **KPIs Executivos Blindados:**
  * **Volume de Inspeções:** Contabilização estrita de formulários finalizados.
  * **Não Conformes (NC):** Total absoluto de desvios operacionais detectados.
  * **Taxa de Conformidade Real:** Cálculo proporcional imune a distorções causadas por itens "Não se Aplica" (N/A).
  * **Tempo Médio Real:** Agrupamento por ID de formulário e eliminação de tempos nulos decorrentes de falhas de sincronização offline.
* **Cobertura (Realizado vs. Meta):** Acompanhamento de inspeções realizadas por aeronave e turno em relação à meta da linha.
* **Mapa de Calor por Slot e Zona de Inspeção:** Identificação imediata de gargalos físicos nos hangares.
* **Desempenho por Líder & Auditoria de Checklist:**
  * *Modo Desvios (Risco):* Rastreamento dos líderes com olhar mais crítico.
  * *Modo N/A (Auditoria Comportamental):* Rastreamento do uso da opção "Não se Aplica" para evitar "canetadas" e aprimorar o desenho dos formulários.
* **Drill-down com Evidências Fotográficas:** Clique em qualquer registro da tabela para inspecionar justificativas, metadados e abrir fotos no Google Drive.
* **Exportação Executiva em CSV:** Download de dados filtrados em formato compatível nativamente com Microsoft Excel (`utf-8-sig` delimitado por ponto-e-vírgula).

---

## Arquitetura do Software
```text
PROJETO-DONOS-DE-AREA/
│
├── .streamlit/
│   ├── config.toml           # Configurações de tema LATAM (Dark Mode oficial)
│   └── secrets.toml          # Credenciais
│
├── assets/                   # Recursos estáticos corporativos
│   ├── icon.png              # Logotipo oficial LATAM
│   └── style.css             # Design System
│
├── src/                      # Código-fonte desacoplado
│   ├── components/           # Camada de Apresentação (UI)
│   │   ├── cards.py          # Renderização de KPIs
│   │   ├── charts.py         # Gráficos interativos com Plotly e @st.fragment
│   │   ├── sidebar.py        # Filtros dinâmicos e controle de estado
│   │   └── tables.py         # Glide Data Grid, busca multi-termo e fotos
│   │
│   ├── services/             # Regras de Negócio e I/O
│   │   ├── business_rules.py # Critérios estritos de formulários
│   │   └── data_loader.py    # Conexão com Google Sheets API e cache seguro
│   │
│   └── utils/                # Utilitários puros
│       └── formatters.py     # Parser universal de tempos e Unicode
│
├── .gitignore                # Proteção contra vazamento de credenciais
├── app.py                    # Orquestrador de fluxo principal
└── requirements.txt          # Dependências
```

## Design System LATAM Airlines

A interface foi personalizada via CSS injetado em conformidade com as diretrizes de acessibilidade WCAG e a paleta oficial da companhia:

| Cor | Hex | Aplicação |
| :--- | :--- | :--- |
| **LATAM Indigo** | `#10004F` / `#2A0088` | Superfícies primárias, cabeçalho e badges institucionais |
| **LATAM Coral** | `#ED1651` / `#E8114B` | Botões de ação, sinalização de não conformidade e alertas |
| **Emerald Green** | `#10B981` | Itens conformes e operação padrão |
| **Slate Gray** | `#64748B` | Itens "Não se Aplica" (N/A) e métricas neutras |

## Segurança da Informação e Compliance
* **Data Loss Prevention:** Nenhuma chave privada, token de acesso ou dado sensível é armazenado em texto puro nos repositórios.
* **Segurança em Nuvem:** A implantação no Streamlit Community Cloud utiliza injeção segura de segredos em tempo de execução via st.secrets.
* **Consumo de API:** Uso de @st.cache_data(ttl=300) e @st.cache_resource para respeitar as cotas de requisição da Google Sheets API sem sobrecarregar a infraestrutura corporativa.

## Mantenedor e Suporte
* **Responsável Técnico:** Saulo Beltrame
* **Unidade:** LATAM MRO — São Carlos (QSC)
* **Canal de Contato:** saulo.junior@latam.com