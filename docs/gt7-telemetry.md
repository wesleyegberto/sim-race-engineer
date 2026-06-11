# Gran Turismo 7 — Telemetry Integration

## Visão Geral

O Gran Turismo 7 (PS5) transmite dados de telemetria em tempo real via **UDP** para a rede local.
O stream é criptografado com **Salsa20** e requer o envio periódico de um pacote de heartbeat
para manter a transmissão ativa.

### Pré-requisito no jogo

Habilitar o envio de dados em:
**Options → Machine Settings → Send Vehicle Data → On**

---

## Protocolo de Rede

| Parâmetro | Valor |
|---|---|
| Protocolo | UDP/IPv4 |
| Porta de recepção (PS5 → cliente) | `33740` |
| Porta de heartbeat (cliente → PS5) | `33739` |
| Tamanho do pacote | `296 bytes` |
| Frequência de envio | ~60 Hz |

### Heartbeat

O PS5 só transmite dados enquanto receber um pacote `b"A"` (1 byte, ASCII) na porta `33739`
a cada **100 ms**. Sem heartbeat, o stream para após alguns segundos.

```
Cliente  ──── b"A" ────▶  PS5:33739   (a cada 100 ms)
Cliente  ◀─── pacote ───  PS5:33740   (~60 Hz)
```

---

## Criptografia

Cada pacote é cifrado com **Salsa20** (stream cipher).

| Parâmetro | Valor |
|---|---|
| Algoritmo | Salsa20 |
| Chave (key) | `Simulator Interface Packet GT7 ver 0.0` (38 bytes, ASCII) |
| Nonce | bytes `[0x40–0x47]` do pacote **criptografado**, invertidos |

### Processo de decifração

```python
nonce = raw_packet[0x40:0x48][::-1]          # 8 bytes, invertidos
cipher = Salsa20.new(key=KEY, nonce=nonce)
decrypted = cipher.decrypt(raw_packet)
```

### Validação do Magic Number

Após decifrar, os primeiros 4 bytes devem ser `0x47375330` (`G75\x30` em little-endian).
Se não baterem, o pacote deve ser descartado.

---

## Estrutura do Pacote (296 bytes, little-endian)

Todos os offsets são em bytes após a decifração.
Tipos: `f32` = float 32-bit, `u8/u16/u32` = unsigned int, `i16/i32/i64` = signed int.

### Identificação

| Offset | Tipo | Campo | Descrição |
|---|---|---|---|
| `0x00` | `u32` | `magic` | Magic number `0x47375330` — valida o pacote |
| `0x68` | `u32` | `packet_id` | Contador monotônico de pacotes (incrementa a cada frame) |

---

### Posição e Movimento

| Offset | Tipo | Campo | Unidade | Descrição |
|---|---|---|---|---|
| `0x04` | `f32×3` | `position` | metros | Posição X, Y, Z do carro no mundo 3D |
| `0x10` | `f32×3` | `velocity` | m/s | Velocidade vetorial X, Y, Z |
| `0x1C` | `f32×3` | `rotation` | rad | Orientação do carro: pitch (X), yaw (Y), roll (Z) |
| `0x28` | `f32×3` | `angular_velocity` | rad/s | Velocidade angular em cada eixo |
| `0x34` | `f32` | `body_height` | metros | Altura do centro de massa em relação ao solo |
| `0x44` | `f32` | `speed` | m/s | Velocidade escalar do carro (pode ser negativa em marcha ré) |

> **Nota:** O eixo Y do GT7 é vertical (cima). A velocidade retornada pode ser negativa
> na marcha ré — use `abs()` para exibição.

---

### Motor e Powertrain

| Offset | Tipo | Campo | Unidade | Descrição |
|---|---|---|---|---|
| `0x38` | `f32` | `engine_rpm` | RPM | Rotação atual do motor |
| `0x80` | `u16` | `min_alert_rpm` | RPM | RPM mínimo de alerta (aproxima-se do idle) |
| `0x82` | `u16` | `max_alert_rpm` | RPM | RPM máximo de alerta (redline do carro atual) |
| `0x84` | `u16` | `calc_max_speed` | km/h | Velocidade máxima calculada para o carro atual (0 = desconhecida) |
| `0x48` | `f32` | `turbo_boost` | bar | Pressão do turbo **acima** de 1 atm (ex: `0.5` = 1.5 bar absoluto) |
| `0xD0` | `f32` | `clutch` | 0–1 | Posição da embreagem (0 = totalmente pressionada, 1 = solta) |
| `0xD4` | `f32` | `clutch_engagement` | 0–1 | Ponto de contato da embreagem |
| `0xD8` | `f32` | `rpm_after_clutch` | RPM | RPM do lado da transmissão (após embreagem) |

---

### Câmbio e Pedais

| Offset | Tipo | Campo | Descrição |
|---|---|---|---|
| `0x88` | `u8` | `gear_byte` | Bits `[3:0]` = marcha atual · Bits `[7:4]` = marcha sugerida |
| `0x89` | `u8` | `throttle` | Posição do acelerador, 0–255 (divide por 255 para 0.0–1.0) |
| `0x8A` | `u8` | `brake` | Posição do freio, 0–255 |
| `0x108` | `f32` | `handbrake` | Freio de mão, 0.0–1.0 |

#### Decodificação da marcha

```
marcha_atual   = gear_byte & 0x0F    # 0=neutra, 1–8=marchas, 15=ré
marcha_sugerida = (gear_byte >> 4) & 0x0F   # 0 = sem sugestão
```

#### Ratios das marchas

| Offset | Campo | Descrição |
|---|---|---|
| `0x10C` | `gear_ratio[0]` | Ratio da ré |
| `0x110` | `gear_ratio[1]` | Ratio da 1ª |
| `0x114–0x128` | `gear_ratio[2–6]` | Ratios das demais marchas (até 8ª) |

---

### Fluidos e Temperaturas

| Offset | Tipo | Campo | Unidade | Observação |
|---|---|---|---|---|
| `0x3C` | `f32` | `fuel_level` | litros | Combustível atual no tanque |
| `0x40` | `f32` | `fuel_capacity` | litros | Capacidade total do tanque |
| `0x4C` | `f32` | `oil_pressure` | bar | Pressão do óleo (multiply × 100 para kPa) |
| `0x50` | `f32` | `water_temp` | °C | Temperatura da água de arrefecimento |
| `0x54` | `f32` | `oil_temp` | °C | Temperatura do óleo do motor |

---

### Pneus — Temperatura de Superfície

Os 4 pneus seguem a ordem **FL · FR · RL · RR** em todos os campos.

| Offset | Campo | Unidade |
|---|---|---|
| `0x58` | `tire_fl_surface_temp` | °C |
| `0x5C` | `tire_fr_surface_temp` | °C |
| `0x60` | `tire_rl_surface_temp` | °C |
| `0x64` | `tire_rr_surface_temp` | °C |

### Pneus — Temperatura Interna (3 zonas)

Cada pneu tem **inner · middle · outer** (interno → externo).

| Offset | Pneu | Campo |
|---|---|---|
| `0xDC–0xE4` | FL | inner, middle, outer (3 × f32) |
| `0xE8–0xF0` | FR | inner, middle, outer |
| `0xF4–0xFC` | RL | inner, middle, outer |
| `0x100–0x107` | RR | inner, middle, outer |

### Pneus — Dinâmica

| Offset | Campo | Unidade | Descrição |
|---|---|---|---|
| `0x9C` | `tire_fl_rps` | rot/s | Velocidade angular da roda FL (negativo = marcha ré) |
| `0xA0` | `tire_fr_rps` | rot/s | Velocidade angular da roda FR |
| `0xA4` | `tire_rl_rps` | rot/s | Velocidade angular da roda RL |
| `0xA8` | `tire_rr_rps` | rot/s | Velocidade angular da roda RR |
| `0xAC` | `tire_fl_radius` | metros | Raio efectivo do pneu FL |
| `0xB0` | `tire_fr_radius` | metros | Raio efectivo do pneu FR |
| `0xB4` | `tire_rl_radius` | metros | Raio efectivo do pneu RL |
| `0xB8` | `tire_rr_radius` | metros | Raio efectivo do pneu RR |
| `0xBC` | `tire_fl_suspension` | metros | Altura de suspensão FL (compressão) |
| `0xC0` | `tire_fr_suspension` | metros | Altura de suspensão FR |
| `0xC4` | `tire_rl_suspension` | metros | Altura de suspensão RL |
| `0xC8` | `tire_rr_suspension` | metros | Altura de suspensão RR |

> **Conversão RPM da roda:** `wheel_rpm = abs(rps) × 60`

---

### Corrida e Volta

| Offset | Tipo | Campo | Unidade | Descrição |
|---|---|---|---|---|
| `0x6C` | `u16` | `lap_count` | — | Número da volta atual |
| `0x6E` | `u16` | `laps_in_race` | — | Total de voltas na corrida (0 = sem limite / não definido) |
| `0x70` | `i32` | `best_lap_ms` | ms | Melhor volta (−1 = sem volta registrada) |
| `0x74` | `i32` | `last_lap_ms` | ms | Última volta completa (−1 = sem volta) |
| `0x78` | `i32` | `time_of_day_ms` | ms | Hora do dia no jogo (desde meia-noite) |
| `0x7C` | `i16` | `race_start_pos` | — | Posição de largada na grade |
| `0x7E` | `i16` | `pre_race_count` | — | Contagem regressiva pré-corrida |

> **Nota:** O `lap_time_ms` (tempo da volta atual em andamento) não está no pacote UDP.
> Deve ser calculado localmente com base no `packet_id` e o timestamp de início da volta.

---

### Plano de Estrada

| Offset | Tipo | Campo | Descrição |
|---|---|---|---|
| `0x8C` | `f32×3` | `road_plane` | Vetor normal do plano da pista sob o carro |
| `0x98` | `f32` | `road_distance` | Distância do centro de massa ao plano da pista |

---

### Identificação do Carro

| Offset | Tipo | Campo | Descrição |
|---|---|---|---|
| `0x124` | `i64` | `car_code` | Identificador numérico do carro no catálogo do GT7 |

---

## Flags de Estado (`0x86`, u16)

Cada bit representa um estado booleano do jogo.

| Bit | Máscara | Nome | Descrição |
|---|---|---|---|
| 0 | `0x0001` | `in_race` | Sessão de corrida/treino ativa |
| 1 | `0x0002` | `paused` | Jogo pausado |
| 2 | `0x0004` | `loading` | Carregando / tela de loading |
| 3 | `0x0008` | `in_gear` | Carro está engatado (não em neutro) |
| 4 | `0x0010` | `has_turbo` | Carro possui turbo |
| 5 | `0x0020` | `rev_limiter` | Limitador de RPM ativo |
| 6 | `0x0040` | `handbrake_active` | Freio de mão acionado |
| 7 | `0x0080` | `lights_on` | Faróis ligados |
| 8 | `0x0100` | `low_beam` | Farol baixo |
| 9 | `0x0200` | `high_beam` | Farol alto |
| 10 | `0x0400` | `asm_active` | ASM (Active Stability Management) atuando |
| 11 | `0x0800` | `tcs_active` | TCS (Traction Control System) atuando |

---

## Campos Não Disponíveis

Os seguintes dados **não** são transmitidos pelo protocolo UDP do GT7:

- Posição na corrida em tempo real (apenas largada em `race_start_pos`)
- Tempo da volta em andamento (deve ser calculado localmente)
- Temperatura dos freios
- Nível de desgaste dos pneus
- Dados de outros carros na corrida
- DRS / ERS / bateria

---

## Referência de Implementação

| Arquivo | Responsabilidade |
|---|---|
| `src/simracing/telemetry/gt7/parser.py` | Decifração Salsa20 + parsing dos 296 bytes |
| `src/simracing/telemetry/gt7/receiver.py` | Socket UDP + loop de heartbeat |
| `src/simracing/telemetry/models.py` | `TelemetryData` — modelo agnóstico de jogo |
| `src/simracing/telemetry/provider.py` | `TelemetryProvider` ABC |
