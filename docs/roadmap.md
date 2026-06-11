# Roadmap — Funcionalidades de Telemetria

Itens ordenados por valor prático para análise de performance em corrida.

---

## 1. G-Meter (Lateral + Longitudinal)

**O que é:** Exibição em tempo real das forças G sentidas pelo piloto — lateral (curvas) e longitudinal (frenagem e aceleração). Representado como um círculo com um ponto móvel (estilo MoTeC/AiM).

**Como calcular:**
- `G_lateral = speed_ms × angular_velocity.y / 9.81`
- `G_longitudinal = Δspeed_ms / Δt / 9.81`

**Onde exibir:** Canto inferior esquerdo, abaixo do gauge de velocidade.

**Status:** ✅ Implementado

---

## 2. Wheel Slip por Roda

**O que é:** Indica se cada roda está escorregando em relação à velocidade real do carro. Valores positivos = wheelspin (rodas girando mais rápido que o esperado, típico de aceleração excessiva). Valores negativos = lockup (rodas girando mais lento, típico de frenagem travada).

**Como calcular:**
```
expected_rps = speed_ms / (2π × tire_radius)
actual_rps   = wheel_rpm / 60
slip_ratio   = (actual_rps - expected_rps) / expected_rps
```

**Onde exibir:** Borda colorida de cada tile de pneu (laranja = wheelspin, ciano = lockup).

**Status:** ✅ Implementado

---

## 3. Indicadores TCS / ASM

**O que é:** Lights indicando quando o sistema eletrônico de controle de tração (TCS) e estabilidade (ASM) estão intervindo. Diretamente disponível nos bits 10 e 11 do campo `flags` do pacote GT7.

**Onde exibir:** Linha de indicadores no header ou painel info.

**Status:** Pendente

---

## 4. Slip Angle / Indicador de Oversteer

**O que é:** Ângulo entre o vetor de velocidade do carro e a direção para a qual ele está apontando. Valor alto = oversteer (traseira saindo). Calculável a partir de `velocity` (espaço mundo) e `rotation` (orientação do carro).

**Como calcular:**
```
car_heading_x = sin(rotation.y)
car_heading_z = cos(rotation.y)
vel_dir = atan2(velocity.x, velocity.z)
car_dir = atan2(car_heading_x, car_heading_z)
slip_angle_deg = (vel_dir - car_dir) × (180/π)
```

**Onde exibir:** Gauge dedicado ou linha numérica no painel info.

**Status:** Pendente

---

## 5. Suspensão (4 Cantos)

**O que é:** Altura de viagem de suspensão em cada roda (FL, FR, RL, RR). Já disponível em `TireData.suspension_height`. Útil para detectar impacto em meio-fios, bottoming, e calibrar molas/amortecedores.

**Onde exibir:** Diagrama de carro visto de cima com barras por canto, ou overlay no tile de pneu.

**Status:** Pendente

---

## 6. Consumo de Combustível (L/volta)

**O que é:** Calcula automaticamente quanto combustível foi consumido por volta, e estima quantas voltas restam com o combustível atual. Essencial para estratégia de pit stop em corridas de endurance.

**Como calcular:**
```
fuel_per_lap = fuel_at_lap_start - fuel_at_lap_end
laps_remaining = current_fuel / fuel_per_lap
```

**Onde exibir:** Painel de informações (lado direito), logo abaixo das linhas de combustível existentes.

**Status:** ✅ Implementado

---

## Métricas Derivadas Futuras

| Métrica | Fonte | Utilidade |
|---|---|---|
| Tempo da volta atual | `packet_id` × Δt desde início da volta | Exibir tempo corrente |
| Velocidade máxima por marcha | `gear_ratios` × `rpm_max` × `radius` | Shift points no tacômetro |
| Clutch slip | `rpm` vs `rpm_after_clutch` | Análise de largada |
| Identificação do carro | `car_code` → tabela de nomes | Exibir nome no header |
