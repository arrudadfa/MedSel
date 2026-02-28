# Tabela dados_cliente (Supabase)

Tabela para persistir os dados coletados durante o fluxo de agendamento. Chave primária: **telefone** (WhatsApp).

## Estrutura

| Coluna                | Tipo        | Origem                                           |
| --------------------- | ----------- | ------------------------------------------------ |
| telefone              | text        | PK, do contexto WhatsApp                         |
| nome_whatsapp         | text        | Info2.NomeWhatsapp                               |
| idpaciente            | integer     | Busca Cadastro ou RAG_Cadastro                   |
| cpf                   | text        | Busca Cadastro                                   |
| nascimento            | text        | Busca Cadastro                                   |
| idconvenio            | integer     | Busca Cadastro ou RAG_Horarios (busca_convenios) |
| idplano               | integer     | Busca Cadastro ou RAG_Horarios (busca_plano)     |
| data_consulta         | text        | Data pretendida                                  |
| idespecialidade       | integer     | RAG_Especialidade                                |
| idprofissional        | integer     | RAG_Profissionais                                |
| idprofissionalhorario | integer     | RAG_Horarios (buscar_horarios)                    |
| data                  | text        | ISO 8601 do horário escolhido                    |
| idagendamento         | integer     | Após RAG_Agendamento                             |
| updated_at            | timestamptz | default now()                                    |

Valores fixos (não persistidos): IdUnidade=2, IdProcedimento=15423, EnviaEmailSms, Telemedicina, AceitaTermoConsentimento.

## Tools n8n

- **buscar_dados** (Supervisor): Supabase "Get row" — consultar o estado atual por telefone.
- **update_dados** (Supervisor e em cada RAG): Supabase "Update row" — Supervisor chama após receber IDs; cada workflow de RAG inclui nó após retorno (merge parcial por telefone).

## SQL de criação

```sql
CREATE TABLE dados_cliente (
  telefone TEXT PRIMARY KEY,
  nome_whatsapp TEXT,
  idpaciente INTEGER,
  cpf TEXT,
  nascimento TEXT,
  idconvenio INTEGER,
  idplano INTEGER,
  data_consulta TEXT,
  idespecialidade INTEGER,
  idprofissional INTEGER,
  idprofissionalhorario INTEGER,
  data TEXT,
  idagendamento INTEGER,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```
