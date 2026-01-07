# 📡 Sentinela: Monitoramento de Rede

Script em Python que monitora a disponibilidade de servidores e dispositivos críticos da rede, registrando o histórico de latência e uptime em um banco de dados.

## 📋 Funcionalidades

- **Ping Automático:** Verifica a conexão com servidores definidos a cada X segundos.
- **Banco de Dados:** Salva o status (`Online`/`Offline`) e a latência (`ms`) em um arquivo SQLite (`sentinela.db`).
- **Histórico:** Permite analisar falhas passadas e serve de base de dados para o Bot de Suporte consultar o status em tempo real.

## 🛠️ Tecnologias

- Python 3.10+
- SQLite (Nativo do Python)
- Bibliotecas: `schedule`, `ping3` (ou a biblioteca de ping utilizada).

## 🚀 Como Rodar

### 1. Instalar Dependências
Abra o terminal na pasta do projeto e instale as bibliotecas necessárias:

```bash
pip install schedule ping3
