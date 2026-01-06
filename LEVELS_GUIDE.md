# Sistema de Niveles y Experiencia - Guía Rápida

## 🎯 Resumen

El bot ahora tiene **dos sistemas paralelos**:

1. **Puntos** - Para comprar en la tienda y desbloquear roles
2. **Niveles (EXP)** - Para progresión y recompensas

## ⭐ Cómo Funciona

### Ganar Experiencia

Los usuarios ganan **15 EXP** por cada mensaje (mismo cooldown que puntos: 60 segundos).

### Fórmula de Niveles

```
EXP necesaria = 100 * (nivel - 1) ^ 1.5
```

**Ejemplos:**
- Nivel 2: 100 EXP
- Nivel 5: 1,146 EXP
- Nivel 10: 7,385 EXP
- Nivel 20: 46,872 EXP
- Nivel 50: 416,333 EXP

### Recompensas por Nivel

**Cada 5 niveles:**
- Puntos bonus = Nivel × 50
  - Nivel 5: 250 puntos
  - Nivel 10: 500 puntos
  - Nivel 20: 1,000 puntos

**Títulos Especiales:**
- Nivel 5: 🌱 Novato
- Nivel 10: ⚔️ Guerrero
- Nivel 15: 🛡️ Veterano
- Nivel 20: 👑 Élite
- Nivel 25: 💎 Maestro
- Nivel 30: 🔥 Leyenda
- Nivel 50: ⭐ Mítico
- Nivel 75: 🌟 Divino
- Nivel 100: 🏆 Inmortal

## 📝 Comandos de Usuario

### `/level [usuario]`
Ver nivel, EXP y progreso al siguiente nivel con barra visual.

**Ejemplo:**
```
⭐ Nivel: 12
🏆 Ranking: #5
💫 EXP Total: 9,234

📈 Progreso al Nivel 13
[████████░░] 
2,345 / 3,000 EXP (78.2%)
Faltan 655 EXP
```

### `/rank [limit]`
Ver ranking de usuarios por nivel (top 10 por defecto, máx 25).

### `/levels`
Ver información sobre el sistema de niveles.

## 🛠️ Comandos de Admin

### `/admin-add-exp @usuario <exp>`
Añadir experiencia a un usuario.

**Ejemplo:**
```
/admin-add-exp @Usuario 500
✅ Se añadieron 500 EXP a @Usuario (Nivel 5 -> 6)
EXP total: 1,500 | Nivel: 6
```

### `/admin-set-level @usuario <nivel>`
Establecer nivel exacto a un usuario.

**Ejemplo:**
```
/admin-set-level @Usuario 20
✅ Nivel de @Usuario establecido a 20
EXP total: 46,872
```

## 📢 Anuncios

Cuando un usuario sube de nivel, se envía un anuncio automático al canal configurado:

```
⭐ ¡LEVEL UP!
@Usuario alcanzó el Nivel 10

🎁 Recompensas
💰 500 puntos bonus
🏆 Título desbloqueado: ⚔️ Guerrero

💫 Nivel Alcanzado: 10
```

## 🔧 Configuración

El sistema de niveles usa las mismas configuraciones que el sistema de puntos:

```env
# En .env
MESSAGE_COOLDOWN=60  # Cooldown compartido con puntos
```

Configuración en código (`level_service.py`):
```python
BASE_EXP = 100           # EXP base para nivel 2
EXP_MULTIPLIER = 1.5     # Multiplicador de dificultad
EXP_PER_MESSAGE = 15     # EXP por mensaje
```

## 💡 Diferencias: Puntos vs Niveles

| Característica | Puntos | Niveles |
|----------------|--------|---------|
| **Propósito** | Moneda para tienda | Progresión y prestigio |
| **Se pueden gastar** | ✅ Sí | ❌ No |
| **Penalización inactividad** | ✅ Sí (-25% a 60 días) | ❌ No |
| **Recompensas** | Roles, items tienda | Puntos bonus, títulos |
| **Comando ver** | `/points` | `/level` |
| **Ranking** | `/leaderboard` | `/rank` |

## 🎮 Ejemplo de Uso Completo

**Usuario envía mensaje:**
```
Usuario: ¡Hola a todos!
```

**Bot (internamente):**
```
✓ +10 puntos otorgados
✓ +15 EXP otorgada
✓ Nivel 9 -> 10 (¡LEVEL UP!)
✓ Recompensas: +500 puntos, título "⚔️ Guerrero"
✓ Anuncio enviado al canal
```

**Usuario ve:**
```
[En canal de anuncios]
⭐ ¡LEVEL UP!
@Usuario alcanzó el Nivel 10
🎁 Recompensas: 💰 500 puntos bonus, 🏆 ⚔️ Guerrero
```

## 📊 Estadísticas

El comando `/admin-stats` ahora también muestra estadísticas de niveles:
- Nivel promedio del servidor
- Usuario con nivel más alto
- Total de EXP ganada en el servidor

---

**¡El sistema de niveles está completamente integrado y funcional!** 🎉
