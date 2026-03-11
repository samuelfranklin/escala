# TASK-018 — Assinatura e Notarização (macOS + Windows)

**Domínio:** INFRA  
**Status:** DONE  
**Prioridade:** P2  
**Depende de:** TASK-016 (GitHub Actions configurado com `release.yml`)  
**Estimativa:** M

---

## Descrição

Configurar assinatura de código e notarização para as plataformas macOS e Windows, garantindo que os instaladores distribuídos não acionem alertas de segurança do sistema operacional.

**macOS**: assinar com *Developer ID Application* e notarizar via `xcrun notarytool` (Apple Notary Service). O `.dmg` e o `.app` interno devem passar na verificação `spctl --assess`.

**Windows**: assinar o `.msi` e o `.exe` (NSIS) com certificado code signing. Em ambiente de desenvolvimento, usar certificado self-signed (sem custo); em produção, substituir por certificado EV (Extended Validation) ou OV de CA reconhecida.

Configurar o `tauri.conf.json` e as variáveis de ambiente do CI para cada plataforma, e documentar o processo completo de geração/renovação de certificados.

---

## Critérios de Aceite

- [ ] Build macOS no CI produz `.dmg` assinado com Developer ID Application
- [ ] `.app` dentro do `.dmg` passa em `spctl --assess --type exec --verbose`
- [ ] `.dmg` é notarizado via `xcrun notarytool submit` e stapled via `xcrun stapler staple`
- [ ] `spctl --assess --type open --context context:primary-signature` retorna `accepted` para o `.dmg`
- [ ] Build Windows no CI produz `.msi` e `.exe` assinados (sem aviso SmartScreen para cert EV em produção)
- [ ] `tauri.conf.json` contém configuração de bundle correta para macOS (`minimumSystemVersion: "12.0"`, `signingIdentity` via env var)
- [ ] Todos os secrets de assinatura documentados em `docs/ops/secrets.md` (sem valores reais)
- [ ] Script `scripts/gen-dev-cert.ps1` gera certificado self-signed para desenvolvimento Windows
- [ ] `CONTRIBUTING.md` descreve o processo de setup de certificados para novos desenvolvedores
- [ ] Build sem secrets de assinatura definidos **não falha** — apenas produz binário não-assinado (comportamento controlado por `if: secrets.APPLE_CERTIFICATE != ''`)

---

## Notas Técnicas

### macOS — Configuração Completa

#### 1. Pré-requisito: Apple Developer Program

- Conta no [Apple Developer Program](https://developer.apple.com) (USD 99/ano)
- Criar certificado **Developer ID Application** no portal de certificados
- Exportar como `.p12` com senha forte

#### 2. Codificar certificado para o CI

