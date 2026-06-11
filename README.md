# Sim Racing Dashboard

Cockpit dashboard em Python para telemetria de jogos de corrida.
Integração inicial com **Gran Turismo 7** (PS5).

## Arquitetura

```
simracing/
├── telemetry/
│   ├── models.py       ← TelemetryData (agnóstico de jogo)
│   ├── provider.py     ← TelemetryProvider (ABC)
│   └── gt7/
│       ├── parser.py   ← Salsa20 decrypt + struct parse
│       └── receiver.py ← UDP socket + heartbeat
└── dashboard/
    ├── app.py          ← pygame event loop + layout
    └── widgets/
        ├── gauge.py        ← velocímetro / tacômetro circular
        ├── bar.py          ← barras throttle / brake / clutch / fuel
        └── tire_widget.py  ← temperaturas dos 4 pneus
```

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Uso

```bash
sim-dashboard --ps5-ip 192.168.1.100
```

O PS5 deve estar na mesma rede. Habilite a telemetria em:
**GT7 → Options → Machine Settings → Send Vehicle Data → enable**

## Adicionar novo jogo

1. Crie `simracing/telemetry/<game>/` com `parser.py` + `receiver.py`
2. Implemente `TelemetryProvider` (connect / disconnect / read)
3. Passe a instância para `DashboardApp` via `main.py`

## Protocolo GT7

- GT7 envia pacotes UDP de 296 bytes na porta **33740**
- Criptografia **Salsa20**, chave `"Simulator Interface Packet GT7 ver 0.0"`
- Requer heartbeat (`b"A"`) a cada ~100 ms para porta **33739**
