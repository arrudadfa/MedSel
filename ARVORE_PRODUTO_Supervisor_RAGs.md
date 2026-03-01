# Árvore de Produto — System Message Supervisor MedSel

Estrutura hierárquica do agente Supervisor e seus RAGs subordinados, com tools e responsabilidades.

---

## Visão geral

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AGENTE BUSCA CADASTRO (pré-Supervisor)                     │
│  CPF → API RealClinic → idpaciente, idconvenio, idplano, data_consulta         │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPERVISOR CONVERSACIONAL                             │
│  Assistente Virtual da Clínica MedSel                                         │
│  • Coleta dados em linguagem natural (nunca menciona IDs)                     │
│  • Delega a RAGs para resolver IDs e executar ações                           │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
    ┌─────────┐               ┌─────────────┐             ┌─────────────┐
    │ RAG_    │               │ RAG_        │             │ RAG_        │
    │ Cadastro│               │ Especialidade│             │ Profissionais│
    └─────────┘               └─────────────┘             └─────────────┘
         │                           │                           │
         │                           │                           │
         ▼                           ▼                           ▼
    ┌─────────┐               ┌─────────────┐             ┌─────────────┐
    │ RAG_    │               │ RAG_        │             │             │
    │ Horarios│◄──────────────│ Agendamento │             │             │
    └─────────┘               └─────────────┘             │             │
                                                          └─────────────┘
```

---

## 1. Supervisor (raiz)

| Atributo | Valor |
|----------|-------|
| **Nome** | Assistente Virtual da Clínica MedSel |
| **Função** | Supervisor Conversacional de Agendamento |
| **Idioma** | pt-BR |

### Responsabilidades
- Conduzir a entrevista com o paciente em linguagem natural
- Delegar a RAGs a resolução de IDs e execução de ações na API RealClinic
- Nunca executar lógica de API nem mencionar IDs ao paciente

### Tools nativas (Supabase n8n)
- **buscar_dados**: Get row de `dados_cliente` por telefone. Usar quando precisar verificar IDs já coletados sem aguardar próxima mensagem.
- **update_dados**: Update row em `dados_cliente`. Chamar após receber IDs de um RAG ou do Busca Cadastro.

### Dados que coleta do paciente (linguagem natural)
- `convenio` — nome do convênio ou "particular"
- `especialidade` — ex.: dermatologia, cardiologia
- `profissional` — nome do médico (opcional)
- `data_desejada` — DD/MM/AAAA
- `horario_preferido` — HH:MM ou período (manhã/tarde)

### Fluxo de decisão
1. Paciente com idpaciente (Busca Cadastro) → não validar CPF, não cadastrar
2. Paciente não encontrado → RAG_Cadastro
3. Particular → IdConvenio = 107, IdPlano = 1293
4. Especialidade informada → RAG_Especialidade
5. Convênio/plano a resolver → RAG_Horarios (busca_convenios, busca_plano)
6. Profissional informado → RAG_Profissionais
7. Data informada → RAG_Horarios (buscar_horarios)
8. Horário escolhido e IDs prontos → RAG_Agendamento

---

## 2. RAGs e suas tools

### 2.1 RAG_Cadastro

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `RAGs/System Message RAG_Cadastro.yaml` |
| **Função** | Cadastrar novo paciente na API RealClinic |
| **Quando** | Paciente não encontrado pelo Busca Cadastro |

#### Tool: `executar_cadastro_api`

| Parâmetro | Tipo | Obrigatório |
|----------|------|:-----------:|
| Nome | string | ✅ |
| DataNascimento | string (ISO 8601) | ✅ |
| CPF | string | ✅ |
| RG | string | ❌ |
| Email | string | ❌ |
| Sexo | NaoInformado \| Masculino \| Feminino | ❌ |
| Celular | string | ❌ |

**Retorno:** IdPaciente, sucesso, mensagem

---

### 2.2 RAG_Especialidade

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `RAGs/System Message RAG_Especialidade.yaml` |
| **Função** | Resolver nome da especialidade → IdEspecialidade |
| **Quando** | Paciente informou nome da especialidade |

#### Tool: `buscar_especialidade`

| Parâmetro | Tipo | Valor |
|----------|------|-------|
| IdUnidade | integer | 2 (fixo) |
| IdConvenio | integer | Definido pela IA (contexto) |

**Payload:** `{"IdUnidade": 2, "IdConvenio": <IA>}`

**Retorno:** IdEspecialidade, nomeNormalizado (IdProcedimento é sempre fixo 15423)

---

### 2.3 RAG_Profissionais

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `RAGs/System Message RAG_Profissionais.yaml` |
| **Função** | Resolver profissional → IdProfissional |
| **Quando** | IdEspecialidade e IdConvenio obtidos |

#### Tool: `buscar_profissionais`

| Parâmetro | Tipo | Valor |
|----------|------|-------|
| IdUnidade | integer | 2 (fixo) |
| IdConvenio | integer | Definido pela IA |
| IdEspecialidade | integer | Definido pela IA |
| IdProcedimento | integer | 15423 (fixo) |

**Payload:** `{"IdUnidade": 2, "IdConvenio": <IA>, "IdEspecialidade": <IA>, "IdProcedimento": 15423}`

**Retorno:** IdProfissional, listaProfissionais [{nome, IdProfissional}]

---

### 2.4 RAG_Horarios

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `RAGs/System Message RAG_Horarios.yaml` |
| **Função** | Resolver convênio/plano e listar horários disponíveis |
| **Quando** | Precisa IdConvenio/IdPlano ou horários |

#### Tool: `busca_convenios`
- **Função:** Buscar/resolver convênios na API RealClinic
- **Quando:** Nome do convênio informado pelo paciente
- **Retorno:** IdConvenio, lista de convênios

#### Tool: `busca_plano`
- **Função:** Buscar/resolver planos na API RealClinic
- **Quando:** Nome do plano informado pelo paciente
- **Retorno:** IdPlano, lista de planos

#### Tool: `buscar_horarios`

| Parâmetro | Tipo | Valor |
|----------|------|-------|
| IdConvenio | integer | Definido pela IA |
| IdEspecialidade | integer | Definido pela IA |
| IdPlano | integer | Definido pela IA |
| Data | string | YYYY-MM-DD ou ISO 8601 |

**Payload:** `{"IdConvenio": <IA>, "IdEspecialidade": <IA>, "IdPlano": <IA>, "Data": "<data>"}`

**Retorno:** horarios [{DataHora, IdProfissional, IdProfissionalHorario}], textoParaPaciente

**Particular:** IdConvenio = 107, IdPlano = 1293

---

### 2.5 RAG_Agendamento

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `RAGs/System Message RAG_Agendamento.yaml` |
| **Função** | Executar agendamento na API RealClinic |
| **Quando** | Todos os IDs necessários disponíveis no contexto |

#### Tool: `executar_agendamento` (POST API)

| Parâmetro | Origem |
|----------|--------|
| IdUnidade | 2 (fixo) |
| IdConvenio | Busca Cadastro ou RAG_Horarios |
| IdEspecialidade | RAG_Especialidade |
| IdPlano | Busca Cadastro ou RAG_Horarios |
| IdProfissional | RAG_Profissionais |
| IdProfissionalHorario | RAG_Horarios (buscar_horarios) |
| IdProcedimento | 15423 (fixo) |
| IdPaciente | Busca Cadastro ou RAG_Cadastro |
| IdAgendamento | 0 |
| Data | YYYY-MM-DDThh:mm:ssZ |
| EnviaEmailSms | true |
| Telemedicina | true |
| AceitaTermoConsentimento | true |

**Endpoint:** `POST https://medsel.realclinic.com.br/medsel/api/AgendamentoIntegracao/Agendar`

**Retorno:** sucesso, mensagem, idAgendamento

---

## 3. Resumo da árvore de tools

```
Supervisor
├── buscar_dados (Supabase Get row - tool nativa n8n)
├── RAG_Cadastro
│   ├── executar_cadastro_api
│   └── update_dados (Supabase Update row - em cada RAG)
├── RAG_Especialidade
│   ├── buscar_especialidade
│   └── update_dados
├── RAG_Profissionais
│   ├── buscar_profissionais
│   └── update_dados
├── RAG_Horarios
│   ├── busca_convenios
│   ├── busca_plano
│   ├── buscar_horarios
│   └── update_dados
└── RAG_Agendamento
    └── executar_agendamento (POST API)
```

---

## 4. Ordem típica de execução

| # | Etapa | RAG / Tool |
|---|-------|------------|
| 0 | Busca Cadastro (antes do Supervisor) | — |
| 1 | Paciente não encontrado | RAG_Cadastro → executar_cadastro_api |
| 2 | Particular | IdConvenio=107, IdPlano=1293 (sem tool) |
| 3 | Especialidade informada | RAG_Especialidade → buscar_especialidade |
| 4 | Convênio/plano a resolver | RAG_Horarios → busca_convenios, busca_plano |
| 5 | Profissional informado | RAG_Profissionais → buscar_profissionais |
| 6 | Data informada | RAG_Horarios → buscar_horarios |
| 7 | Horário escolhido | RAG_Agendamento → executar_agendamento |
