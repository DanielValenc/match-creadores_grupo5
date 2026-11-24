# TrueMatch AI

**Inteligencia de creadores para marcas.** Analiza el perfil público de un creador de TikTok y entrega a una marca su perfil Big Five con citas verificadas, una auditoría de audiencia (Ley de Benford) y los sectores comerciales con los que encaja.

*Proyecto académico · Universidad Central del Ecuador · Dispositivos Móviles · Grupo 5*

> Los resultados son estimaciones automáticas con fines educativos. No son un diagnóstico psicológico ni una auditoría certificada.

## Integrantes

| Integrante | Aporte |
|---|---|
| Nicolás Caiza | Arquitectura DDD, backend en capas y app móvil |
| Daniel Valencia | Scraper original, guía técnica y revisión de pull requests |
| Jair Folleco | Dashboard web (Flask) y prototipo en Figma |
| Karen García | Estructura académica y reporte de evidencia |

## Arranque rápido

Requisitos: Python 3.10+, Node.js LTS y Expo Go en el celular.

**Backend y web**

```bash
python -m venv venv && source venv/Scripts/activate   # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt && playwright install chromium
echo "GROQ_API_KEY=tu_clave" > .env                   # clave de console.groq.com
cd backend
python -m truematch.interfaces.cli.main session       # una sola vez: iniciar sesión en TikTok
python -m truematch.interfaces.cli.main web           # http://127.0.0.1:5000
```

**App móvil**

```bash
cd mobile && npm install
cp .env.example .env.local     # editar EXPO_PUBLIC_API_URL=http://TU_IP:5000
npx expo start -c              # escanear el QR con Expo Go
```

## Documentación

| Recurso | Enlace |
|---|---|
| Confluence (documentación completa) | [Espacio TrueMatch AI – Grupo 5](https://uce-team-ndyuvdu6.atlassian.net/wiki/x/1gAE) · [Guía técnica](https://uce-team-ndyuvdu6.atlassian.net/wiki/spaces/TM/pages/851982) |
| Jira (tareas y sprints) | [Tablero](https://uce-team-ndyuvdu6.atlassian.net/jira/software/projects/TM/boards/1) |
| Figma (prototipo) | [Prototipo-APP](https://www.figma.com/design/vhSjNmPShuKV5hoIjUKBZa/Prototipo-APP?node-id=0-1) |