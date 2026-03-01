# Agentes RAG Subordinados - MedSel

Estes agentes RAG acessam a API RealClinic e retornam ao Supervisor os IDs necessários para o agendamento. O Supervisor **nunca** expõe esses IDs ao paciente.

## Tools nativas (Supabase n8n)

- **buscar_dados** (Supervisor): Get row de `dados_cliente` por telefone. Permite verificar IDs já coletados sem aguardar próxima mensagem.
- **update_dados** (em cada RAG): Update row em `dados_cliente`. Cada workflow de RAG deve incluir nó Supabase após retorno. Ver `docs/DADOS_CLIENTE_TABELA.md`.

## Resumo dos RAGs

| RAG | Função | Entrada | Saída |
|-----|--------|---------|-------|
| RAG_Cadastro | Cadastrar paciente novo | Nome, DataNascimento, CPF | IdPaciente |
| RAG_Especialidade | Resolver especialidade | nomeEspecialidade | IdEspecialidade, IdProcedimento=15423 |
| RAG_Profissionais | Resolver profissional | IdEspecialidade, nomeProfissional | IdProfissional |
| RAG_Horarios | busca_convenios, busca_plano, buscar_horarios | nomeConvenio/plano ou IdConvenio, IdEspecialidade, IdPlano, Data | IdConvenio, IdPlano, horários + IdProfissionalHorario |
| RAG_Agendamento | Executar agendamento | payload completo | confirmação/erro |

## Ordem de execução típica

1. Busca Cadastro (antes do Supervisor) → idpaciente, idconvenio, idplano
2. Se não encontrado → RAG_Cadastro
3. Particular → IdConvenio = 107, IdPlano = 1293
4. RAG_Especialidade
5. RAG_Horarios (busca_convenios, busca_plano) — se precisar resolver convênio/plano
6. RAG_Profissionais
7. RAG_Horarios (buscar_horarios)
8. RAG_Agendamento

## API RealClinic

- **Agendamento**: `POST https://medsel.realclinic.com.br/medsel/api/AgendamentoIntegracao/Agendar`
- Demais endpoints devem ser configurados conforme documentação da API.
