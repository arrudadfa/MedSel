# Agentes RAG Subordinados - MedSel

Estes agentes RAG acessam a API RealClinic e retornam ao Supervisor os IDs necessários para o agendamento. O Supervisor **nunca** expõe esses IDs ao paciente.

## Resumo dos RAGs

| RAG | Função | Entrada | Saída |
|-----|--------|---------|-------|
| RAG_Cadastro | Cadastrar paciente novo | Nome, DataNascimento, CPF | IdPaciente |
| RAG_Convenio_Plano | Resolver convênio/plano (paciente novo) | nomeConvenio, nomePlano | IdConvenio, IdPlano |
| RAG_Convenios_Disponiveis | Listar convênios da especialidade | IdUnidade=2, IdEspecialidade, IdProfissional=0 | lista de convênios |
| RAG_Especialidade | Resolver especialidade | nomeEspecialidade | IdEspecialidade, IdProcedimento |
| RAG_Profissionais | Resolver profissional | IdEspecialidade, nomeProfissional | IdProfissional |
| RAG_Horarios | Listar horários disponíveis | IdProfissional, dataDesejada | horários + IdProfissionalHorario |
| RAG_Agendamento | Executar agendamento | payload completo | confirmação/erro |

## Ordem de execução típica

1. Busca Cadastro (antes do Supervisor) → idpaciente, idconvenio, idplano
2. Se não encontrado → RAG_Cadastro
3. Se paciente novo sem convênio → RAG_Convenio_Plano
4. Particular → IdConvenio = 0 (sem busca)
5. RAG_Especialidade
6. RAG_Convenios_Disponiveis (listar convênios da especialidade)
5. RAG_Profissionais
6. RAG_Horarios
7. RAG_Agendamento

## API RealClinic

- **Agendamento**: `POST https://medsel.realclinic.com.br/medsel/api/AgendamentoIntegracao/Agendar`
- Demais endpoints devem ser configurados conforme documentação da API.
