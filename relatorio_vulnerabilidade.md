# Relatório de Vulnerabilidades — Tech Challenge Fase 4

| Item | Valor |
|---|---|
| Data da análise | 03/11/2026 |
| Escopo | `tc-oficina-os-service`, `tc-oficina-billing-service`, `tc-oficina-execution-service` |
| Commits avaliados | OS `66e8d36` · Billing `16f2f9d` · Execution `ffb15ca` |
| Ferramenta principal | SonarCloud (organização `rtmaraujo`) |
| Complemento | Revisão manual de configuração, webhook, segredos e infraestrutura |
| Ambiente | `http://44.253.115.185` (k3s na AWS) |

## 1. Resumo executivo

Os três projetos estão com **Quality Gate aprovado** no SonarCloud, **nenhuma vulnerabilidade aberta**, **nenhum security hotspot aberto** e **Security Rating A**. A análise estática foi complementada por revisão manual dos pontos de maior risco: webhook de pagamento, gestão de segredos, exposição de bancos e configuração do cluster.

Não foi encontrada vulnerabilidade crítica ou alta no código dos três serviços. O principal risco identificado é de **configuração do ambiente de laboratório**: as APIs estão publicadas sem autenticação e sem TLS. Esse risco é aceitável no contexto do desafio, mas está registrado com recomendação de correção antes de qualquer uso em produção.

## 2. Resultado por projeto (SonarCloud)

| Projeto | Quality Gate | Vulnerabilidades | Security Hotspots | Security Rating | Cobertura de linha | Cobertura de branch |
|---|---|---|---|---|---|---|
| OS Service | **OK** | **0** | **0** | **A (1.0)** | 99,5% | 96,4% |
| Billing Service | **OK** | **0** | **0** | **A (1.0)** | 98,6% | 91,7% |
| Execution Service | **OK** | **0** | **0** | **A (1.0)** | 97,7% | 90,4% |

- Security hotspots revisados: **100%** nos três projetos (nenhum pendente).
- Issues do tipo `VULNERABILITY` abertas: **0** nos três projetos.
- Quality Gate bloqueante no pipeline (`-Dsonar.qualitygate.wait=true`): um merge na `main` não passa se o gate falhar.

**Links dos projetos:**

- https://sonarcloud.io/project/overview?id=rtmaraujo_tc-oficina-os-service
- https://sonarcloud.io/project/overview?id=rtmaraujo_tc-oficina-billing-service
- https://sonarcloud.io/project/overview?id=rtmaraujo_tc-oficina-execution-service

## 3. Controles de segurança verificados

| Controle | Evidência |
|---|---|
| Segredos fora do versionamento | `/k8s/secret.yaml` está no `.gitignore` dos três repositórios; segredos são criados no cluster via `kubectl create secret` e as credenciais de CI ficam em GitHub Secrets |
| Credenciais no pipeline | Valores passam por `env:` e não são interpolados diretamente em `run:` (evita exposição em logs — Sonar S7636) |
| Assinatura do webhook | `MercadoPagoPaymentGateway.validarAssinatura` usa HMAC-SHA256 sobre `id:<data.id>;request-id:<x-request-id>;ts:<ts>;` e comparação em tempo constante com o `v1` do header `x-signature` |
| Webhook sem confiança no corpo | O controller valida a assinatura antes de processar, ignora tipos diferentes de `payment` e só conclui com estados finais (`approved`, `rejected`, `cancelled`, `refunded`, `charged_back`) |
| Estados intermediários | Pagamentos `pending`/`in_process` respondem `200 pendente` sem publicar evento, evitando compensar uma OS que ainda pode ser paga |
| Log injection | O webhook não registra o corpo da requisição, apenas o tamanho (Sonar S5145) |
| Isolamento de dados | Um banco por serviço; RDS PostgreSQL em subnets privadas e MongoDB via Service interno do cluster (sem exposição externa) |
| Consistência da Saga | Idempotência por `evento_processado(event_id, topico)` e `.DLT` por tópico consumido |
| Validação de build | `mvn verify` com `jacoco:check` (mínimo de 85% de LINE e BRANCH) e Quality Gate obrigatório no PR |

## 4. Riscos identificados e recomendações

| # | Risco | Severidade | Situação | Recomendação |
|---|---|---|---|---|
| 1 | APIs publicadas sem autenticação/autorização | Média (alta em produção) | Aceito no ambiente de laboratório do desafio | Adicionar OAuth2/JWT ou mTLS, com papéis por serviço, antes de expor em produção |
| 2 | Tráfego HTTP sem TLS no IP público | Média | Aceito no laboratório | Publicar atrás de HTTPS (ACM/Let's Encrypt) e redirecionar HTTP para HTTPS |
| 3 | Segredos do Kubernetes apenas em `Secret` base64 | Baixa | Aceito no laboratório | Migrar para External Secrets, AWS Secrets Manager ou IRSA |
| 4 | Ausência de rate limiting/WAF na borda | Baixa | Aceito no laboratório | Aplicar middleware de rate limit no Traefik e WAF na borda |
| 5 | Pipeline sem análise de dependências (SCA) | Baixa | Não implementado | Adicionar OWASP Dependency-Check ou Trivy no `mvn verify`/pipeline |

Nenhum desses itens é uma vulnerabilidade explorável no código de negócio; são decisões de configuração do ambiente de demonstração. O item 1 é o de maior prioridade para uma evolução do sistema.

## 5. Histórico

O relatório da fase anterior (jul/2026) registrou **1 security hotspot CWE-639** (authorization bypass) corrigido no sistema monolítico. Na Fase 4, a análise dos três microsserviços foi refeita e o resultado atual é **0 vulnerabilidades e 0 hotspots abertos**, com Security Rating A nos três projetos.

## 6. Conclusão

A entrega da Fase 4 passa na análise de segurança estática do SonarCloud, com Quality Gate aprovado, cobertura acima de 85% e controles relevantes implementados no fluxo de pagamento e na gestão de segredos. Os riscos remanescentes são de configuração do ambiente de laboratório e estão documentados com recomendações objetivas.
