# Roteiro do Vídeo — Overview da Aplicação — Tech Challenge Fase 4

**Duração alvo:** 9 a 10 minutos
**Participante:** Marcos da Paz Araujo
**Ambiente:** `http://44.253.115.185` (k3s na AWS)
**Documentação:** https://github.com/rtmaraujo/tc-oficina-docs

> **Formato deste vídeo:** overview da aplicação, não uma execução do fluxo completo. A ideia é apresentar a arquitetura, o código, a Saga, o pagamento, o CI/CD e as evidências já coletadas. Não é necessário criar uma OS nova nem chegar em `FINALIZADA` durante a gravação.

> Dica: grave em 1080p, feche abas desnecessárias e deixe abertos apenas o repositório de documentação, os repositórios dos serviços, o GitHub Actions, o SonarCloud, o Grafana/Zipkin e um terminal. Fale devagar e mostre a tela antes de explicar o "como".

---

## Bloco 0 — Abertura (0:00 – 0:45)

**Tela:** README do repositório `tc-oficina-docs` no GitHub.

**Fala sugerida:**

> "Olá, eu sou o Marcos da Paz Araujo e este é o Tech Challenge da Fase 4 da Oficina Mecânica. Nesta fase eu evoluí o sistema para três microsserviços independentes — OS, Billing e Execution — integrados por Kafka com uma Saga orquestrada, deploy automatizado na AWS e observabilidade com Prometheus, Grafana e Zipkin. Neste vídeo eu vou fazer um overview da aplicação: arquitetura, organização do código, Saga, pagamento, pipelines, ambiente no ar e evidências. O fluxo completo já foi executado e está registrado no repositório de documentação, então não vou repetir a execução aqui."

Mostre rapidamente o índice do README: relatório, arquitetura, Postman, evidências e relatório de vulnerabilidades.

---

## Bloco 1 — Mapa da entrega e repositórios (0:45 – 2:00)

**Tela:** README do `tc-oficina-docs`, seção **Repositórios**, e depois a lista de repositórios no GitHub.

**Mostre e comente:**

- **Quatro repositórios:** três serviços e um repositório só de documentação.
- Cada serviço tem **banco próprio**, `Dockerfile`, manifestos Kubernetes e pipeline de CI/CD independentes.
- O `tc-oficina-docs` concentra o que é comum à entrega: relatório, PDF, arquitetura, diagramas, Postman, evidências e análise de vulnerabilidades.
- Divisão de responsabilidades:
  - **OS Service:** ciclo de vida da ordem de serviço e orquestração da Saga.
  - **Billing Service:** orçamento, aprovação e pagamento.
  - **Execution Service:** diagnóstico, reparo e finalização da execução.

**Fala sugerida:**

> "A primeira decisão foi separar o sistema em três serviços com repositórios e bancos independentes. O OS Service é o orquestrador; o Billing cuida de orçamento e pagamento; o Execution cuida da execução e do diagnóstico. A documentação fica em um quarto repositório, para não misturar conteúdo geral com o código de cada serviço."

---

## Bloco 2 — Arquitetura da solução (2:00 – 3:20)

**Tela:** `ARQUITETURA.md` no repositório de documentação, com o diagrama geral (PNG ou Mermaid renderizado).

**Mostre e comente:**

- Cliente → **Traefik** → três serviços, cada um com seu banco.
- **PostgreSQL** para OS e Billing (RDS) e **MongoDB** para Execution.
- Comunicação **assíncrona por Kafka**; não há chamada síncrona entre os serviços.
- **Saga orquestrada no OS Service:** ele mantém a máquina de estados, decide os próximos passos e dispara compensações.
- **Billing e Execution são participantes:** consomem comandos e publicam o resultado.
- **Idempotência** por `evento_processado` e **DLT** por tópico consumido.
- Tabelas `saga_instancia`, `saga_passo` e `ordem_servico_historico` como trilha de auditoria.
- Observabilidade no namespace `monitoring`: Prometheus, Grafana e Zipkin.

**Fala sugerida:**

> "A escolha por orquestração foi para ter um ponto único de decisão e auditoria. Cada passo da Saga é gravado, então eu consigo reconstruir exatamente o que aconteceu com uma ordem de serviço, inclusive quando ela é compensada. A comunicação é toda por eventos, e cada serviço tem o seu próprio banco — não existe acesso cruzado a banco entre eles."

---

## Bloco 3 — Organização do código e contratos (3:20 – 4:40)

**Tela:** repositório do **OS Service** no GitHub.

**Mostre:**

1. A estrutura em camadas:
   ```
   presentation → application → domain ← infrastructure
                                   └── config (listeners Kafka, error handler)
   ```
2. A classe `SagaOrchestrator` (ou o pacote de orquestração) e os listeners Kafka.
3. As entidades/tabelas da Saga: `saga_instancia`, `saga_passo`, `ordem_servico_historico`, `evento_processado`.
4. No **Billing**, a porta `PaymentGateway` e a implementação `MercadoPagoPaymentGateway`.
5. No **Execution**, o listener de `execution-requested` e a publicação de `order-progress` / `order-finalized`.

**Tela (opcional, ao vivo):** Swagger UI de um dos serviços:

- `http://44.253.115.185/os/swagger-ui/index.html`
- `http://44.253.115.185/billing/swagger-ui/index.html`
- `http://44.253.115.185/execution/swagger-ui/index.html`

**Fala sugerida:**

> "Os três serviços seguem o mesmo desenho em camadas: o controller não conhece persistência, a camada de aplicação concentra os casos de uso e o domínio fica isolado. No Billing, o pagamento fica atrás de uma porta, então o caso de uso não sabe se o provedor é Mercado Pago ou uma implementação local. No OS, o orquestrador concentra as transições e a compensação."

---

## Bloco 4 — Saga e evidências (4:40 – 6:20)

**Tela:** `ARQUITETURA.md`, seções da Saga (sequência e máquina de estados).

**Mostre e comente:**

- Máquina de estados:
  ```
  ABERTA → ORCAMENTO_GERADO → APROVADA → PAGA → EXECUCAO → CONCLUIDA → FINALIZADA
                                      ↘ CANCELADA (compensação)
  ```
- Cenários cobertos:
  1. **Fluxo feliz:** orçamento gerado, aprovado, pago, execução e finalização.
  2. **Orçamento rejeitado:** compensação do orçamento e OS `CANCELADA`.
  3. **Pagamento recusado:** compensação e OS `CANCELADA`.
- Compensação publica `compensate-budget`, `compensate-execution` e `saga-compensated`.
- Idempotência: se o mesmo evento chegar duas vezes, nada é republicado.

**Tela:** arquivo de evidência no repositório de documentação:

`evidencias/saga-evidence-2026-11-03.txt`

Mostre os números:

- **10 sagas** registradas: **4 `CONCLUIDA`** e **6 `COMPENSADA`**.
- **44 passos** em `saga_passo`.
- Eventos processados nos **7 tópicos** consumidos (`budget-generated`, `budget-approved`, `budget-rejected`, `payment-completed`, `payment-failed`, `order-progress`, `order-finalized`).

**Demo curta opcional (sem executar o fluxo):** mostre novamente a saída do job de evidência:

```bash
kubectl logs -n oficina-os job/saga-evidence
```

Destaque as 10 sagas, os 44 passos e os 7 tópicos processados.

**Fala sugerida:**

> "Essas evidências foram coletadas direto do banco do OS Service. São dez sagas executadas, quatro concluídas e seis compensadas, com quarenta e quatro passos registrados. Os dois cenários de compensação — orçamento rejeitado e pagamento recusado — estão comprovados aqui, e o histórico mostra cada transição com o sagaId. Por isso eu não preciso repetir o fluxo durante o vídeo."

---

## Bloco 5 — CI/CD, testes e qualidade (6:20 – 7:35)

**Tela:** GitHub → **Actions** do `tc-oficina-os-service`, run verde do merge mais recente.

**Mostre:**

1. Workflow **CI/CD Pipeline - OS Service** concluído com sucesso.
2. Job **Build, testes, cobertura e SonarCloud**:
   - `Tests run: 66, Failures: 0` no OS; total da entrega: **200 testes** (OS 66, Billing 90, Execution 44).
   - `jacoco:check` com mínimo de **85% de LINE e BRANCH**.
   - SonarCloud com Quality Gate aguardado (`-Dsonar.qualitygate.wait=true`).
3. Job **Imagem no ECR e deploy no k3s**: build/push da imagem com a tag do commit e `kubectl rollout status`.
4. Aba **Branches**: `main` protegida com PR obrigatório e check **Build, testes, cobertura e SonarCloud**.
5. Pull requests mergeados: OS **#8**, Billing **#8**, Execution **#7**.

**Tela:** SonarCloud dos três projetos.

- Quality Gate **Passed**.
- **0 vulnerabilidades**, **0 security hotspots** abertos e Security Rating **A**.
- Link para o relatório de vulnerabilidades no repositório de documentação.

**Fala sugerida:**

> "Nenhum commit vai direto na main. Todo merge passa por PR com o check obrigatório, que roda os testes, valida a cobertura mínima de 85% e espera o Quality Gate do SonarCloud. Só depois a imagem é publicada no ECR e o deploy acontece automaticamente no Kubernetes. A entrega fechou com duzentos testes e zero falhas nos três serviços."

---

## Bloco 6 — Serviços no ar e observabilidade (7:35 – 8:45)

**Tela:** navegador com os health checks, abertos em sequência:

- `http://44.253.115.185/os/actuator/health`
- `http://44.253.115.185/billing/actuator/health`
- `http://44.253.115.185/execution/actuator/health`

Mostre os três respondendo `UP` e comente que cada deployment está com **2 réplicas**.

**Tela:** Grafana → `http://44.253.115.185/grafana/` → dashboard **Oficina Fase 4 - Microsservicos**.

- Requisições por segundo dos três serviços.
- Latência p95.
- Erros 5xx.
- Heap JVM.
- Ajuste o período para **Last 6 hours** ou **Last 15 minutes** para mostrar o tráfego.

**Tela:** Zipkin → `http://44.253.115.185/zipkin/`.

- Busque por `tc-oficina-os-service` e abra um trace.
- Mostre as spans atravessando OS, Billing e Execution.
- Destaque o `sagaId` nos logs/tags.

**Tela (opcional):** Prometheus → `http://44.253.115.185/prometheus/graph` → Status → Targets (3 `up`).

**Fala sugerida:**

> "Os três serviços estão no ar com duas réplicas cada. No Grafana eu acompanho requisições, latência, erros e memória por serviço; no Zipkin eu vejo o trace distribuído de uma requisição atravessando os três serviços, com o sagaId correlacionando os logs. Isso fecha o requisito de observabilidade."

---

## Bloco 7 — Pagamento com Mercado Pago (8:45 – 9:30)

**Tela (terminal):** confirme o provider ativo:

```bash
kubectl get configmap billing-service-config -n oficina-billing \
  -o jsonpath="{.data.PAGAMENTO_PROVIDER}"
```

Resultado esperado: `mercadopago`.

**Tela:** `MercadoPagoPaymentGateway` no repositório do Billing.

Mostre e comente:

- `criarCheckout` chama `POST /checkout/preferences` do **Checkout Pro** e devolve `preferenceId` + `initPoint`.
- `consultarPagamento` chama `GET /v1/payments/{id}` antes de concluir.
- `validarAssinatura` valida o webhook com **HMAC-SHA256**.
- O webhook ignora tipos diferentes de `payment`, só processa estados finais e responde `200 pendente` para `pending`/`in_process`.
- A porta `PaymentGateway` isola o provedor: trocar de provider não altera os casos de uso nem a Saga.

**Opcional:** mostre o `preferenceId` de uma preferência real já criada, deixando claro que o pagamento **não foi concluído**. Não simule um pagamento aprovado no vídeo.

**Fala sugerida:**

> "O provider real do Mercado Pago está ativo no cluster. O Billing cria a preferência no Checkout Pro, consulta o pagamento antes de concluir e valida a assinatura do webhook. O pagamento fica atrás da porta PaymentGateway, então o resto do sistema não depende do provedor. A integração está pronta e uma preferência real já foi gerada; o pagamento em si não foi concluído, e eu não vou simular isso aqui."

---

## Bloco 8 — Encerramento (9:30 – 10:00)

**Tela:** README do `tc-oficina-docs` ou slide final.

**Fala sugerida:**

> "Resumindo a entrega: três microsserviços independentes, cada um com banco, imagem e pipeline próprios; uma Saga orquestrada com compensação, idempotência, DLQ e auditoria; duzentos testes automatizados com cobertura acima de 85%; Quality Gate aprovado nos três projetos; deploy automatizado na AWS; observabilidade com Prometheus, Grafana e Zipkin; e o provider real do Mercado Pago ativo no cluster. Tudo está documentado no repositório tc-oficina-docs, com relatório, PDF, arquitetura, Postman e evidências. Obrigado!"

---

## Checklist antes de gravar

- [ ] README do `tc-oficina-docs` aberto, com os links de relatório, arquitetura, Postman e vulnerabilidades.
- [ ] Os três repositórios de serviço abertos em abas separadas.
- [ ] Run do GitHub Actions já concluído e aberto (plano B do deploy).
- [ ] SonarCloud aberto nos três projetos, com Quality Gate visível.
- [ ] Health checks respondendo (`/os`, `/billing`, `/execution`).
- [ ] Grafana com dados das últimas 6 horas.
- [ ] Zipkin com pelo menos um trace recente.
- [ ] Arquivo `evidencias/saga-evidence-2026-11-03.txt` aberto.
- [ ] Terminal com `kubectl` configurado e o comando do configmap testado.
- [ ] Nenhuma execução de fluxo novo planejada — o vídeo é overview.
- [ ] Notificações do Windows silenciadas; abas extras fechadas.
- [ ] Teste de áudio de 10 segundos antes da gravação final.

## Plano B (se algo falhar ao vivo)

| Problema | Contorno |
|---|---|
| Cluster reiniciando pods | Mostrar o histórico de evidências já coletado e o log do job `saga-evidence` |
| GitHub Actions lento | Usar um run já concluído; não é necessário disparar deploy novo |
| Grafana sem dados recentes | Ampliar o período para 6h/24h e usar os painéis de heap e requisições |
| Zipkin sem traces | Abrir diretamente um trace pelo ID capturado antes da gravação |
| `kubectl` sem resposta | Mostrar o configmap e o código do provider; não é necessário alterar nada no cluster |
| SonarCloud indisponível | Usar as capturas do relatório de vulnerabilidades e os números do relatório da entrega |
| Mercado Pago sem preferência nova | Mostrar o código, o configmap e a preferência já criada; não simular pagamento |
