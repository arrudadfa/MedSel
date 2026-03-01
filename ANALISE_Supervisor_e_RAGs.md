# Análise do System Message Supervisor e Proposta de Arquitetura RAG

## 1. Análise do System Message Atual

### Pontos Fortes
- **Objetivo claro**: Coletar informações e delegar execução via tools
- **Regras de comunicação**: Não mencionar IDs, não repetir perguntas
- **Separação de responsabilidades**: Supervisor não executa lógica de API manualmente

### Problemas Identificados

| Problema | Descrição | Supervisor original | Supervisor refatorado |
|----------|-----------|:-------------------:|:---------------------:|
| **Acoplamento** | O Supervisor lista 10 tools diretamente, misturando responsabilidades de orquestração e resolução de dados  | ✅ Resolvido — delega a 5 RAGs |
| **Exposição de conceitos técnicos** | `required_states` menciona `id_especialidade`, `id_convenio` — o Supervisor não deveria conhecer IDs  | ✅ Resolvido — coleta nomes, RAGs resolvem IDs |
| **Fluxo redundante** | `validar_cpf` e `buscar_paciente` são feitos pelo agente Busca Cadastro *antes* do Supervisor  | ✅ Resolvido — não valida CPF nem busca paciente |
| **Inconsistência com dados recebidos** | O Busca Cadastro já fornece `idpaciente`, `idconvenio`, `idplano`, `data_consulta` — o Supervisor não precisa buscar novamente  | ✅ Resolvido — `contexto_recebido` documenta isso |
| **Falta de distinção** | Não diferencia claramente o que o paciente informa (nomes) do que vem da API (IDs)  | ✅ Resolvido — `dados_para_coletar` vs `delegacao_rags` |

**Resumo:** Os problemas **persistem** no `System Message Supervisor.yaml` (original). No `System Message Supervisor (refatorado).yaml`, todos foram **resolvidos**.

### Dados que o Supervisor Recebe do Agente Busca Cadastro

**Paciente cadastrado:**
- Nome no Perfil, Telefone, idpaciente, CPF, Data de nascimento
- IdConvenio, IdPlano (já resolvidos)
- Data pretendida para agendamento

**Paciente não cadastrado:**
- Fluxo: `cadastro_novo` → coletar nomeCompleto, dataNascimento, telefone

---

## 2. Arquitetura Proposta: Supervisor + RAGs

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTE BUSCA CADASTRO                         │
│  (CPF → API RealClinic → idpaciente, idconvenio, idplano, etc.)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUPERVISOR (limpo)                             │
│  • Recebe dados do paciente (IDs já resolvidos quando aplicável)  │
│  • Coleta do paciente: especialidade, médico, data, horário        │
│  • NUNCA menciona IDs ao paciente                                 │
│  • Delega a RAGs para resolver IDs e executar agendamento         │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│ RAG_Especial │    │ RAG_Profiss  │    │ RAG_Horarios     │
│ nome → IdEsp │    │ nome → IdProf│    │ data → IdHorario │
└──────────────┘    └──────────────┘    └──────────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                    ┌──────────────────┐
                    │ RAG_Agendamento  │
                    │ POST API RealClinic│
                    └──────────────────┘
```

---

## 3. Mapeamento: Dados do Paciente ↔ IDs da API

| Dado que o Supervisor coleta do paciente | RAG que resolve | Campo no payload de agendamento |
|-----------------------------------------|-----------------|----------------------------------|
| Nome da especialidade | RAG_Especialidade | IdEspecialidade |
| Nome do médico/profissional | RAG_Profissionais | IdProfissional |
| Data e horário escolhidos | RAG_Horarios | IdProfissionalHorario, Data |
| (já vem do Busca Cadastro) | — | IdPaciente, IdConvenio, IdPlano |
| Nome do convênio/plano | RAG_Horarios (busca_convenios, busca_plano) | IdConvenio, IdPlano |
| — | — | IdProcedimento = 15423 (fixo) |

**Valores fixos no payload:**
- IdUnidade: 2
- IdProcedimento:15423
- IdAgendamento: 0
- EnviaEmailSms, Telemedicina, AceitaTermoConsentimento: true

**Valores fixos no payload para atendimento no particular:**
- IdConvenio: 107
- IdPlano: 1293

---

## 4. Fluxo de Decisão do Supervisor (Simplificado)

1. **Paciente identificado** (dados do Busca Cadastro) → usar idpaciente, idconvenio, idplano
2. **Paciente não cadastrado** → acionar RAG_Cadastro (ou tool cadastro_novo)
3. **Especialidade** → coletar nome, acionar RAG_Especialidade → IdEspecialidade
4. **Profissional** → coletar nome (ou primeiro disponível), acionar RAG_Profissionais → IdProfissional
5. **Data/Horário** → coletar preferência, acionar RAG_Horarios → IdProfissionalHorario, Data
6. **Todos os IDs prontos** → acionar RAG_Agendamento

---

## 5. Regras Críticas para o Supervisor

- **NUNCA** solicitar ou informar ao paciente: IdPaciente, IdConvenio, IdPlano, IdEspecialidade, IdProfissional, IdProfissionalHorario, IdProcedimento
- **SEMPRE** falar em termos humanos: "qual especialidade?", "qual médico?", "qual data e horário?"
- **SEMPRE** delegar a um RAG quando precisar de um ID para prosseguir
