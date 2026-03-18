---
name: notebooklm-writer
description: Permite listar notebooks de Google NotebookLM y generar artículos profesionales basados en sus fuentes y notas. Úsalo para automatizar la creación de contenido desde tus notebooks de investigación.
---

# 📝 NotebookLM Writer

Esta skill permite conectar Gemini CLI con tus notebooks de Google NotebookLM para extraer datos y escribir artículos.

## 🚀 Inicio Rápido

Para usar esta skill, necesitas tu token de sesión de NotebookLM.

### Cómo obtener tu Token (`__Host-GAPS`):
1. Ve a [notebooklm.google.com](https://notebooklm.google.com).
2. Abre las herramientas de desarrollador (`F12` o `Click derecho > Inspeccionar`).
3. Ve a la pestaña **Aplicación (Application)** > **Cookies** > `https://notebooklm.google.com`.
4. Busca la cookie llamada **`__Host-GAPS`**. Copia su valor.
5. Pásame este token cuando me pidas listar o leer tus notebooks.

## 📂 Flujos de Trabajo

### 1. Listar Notebooks
Pídeme: *"Lista mis notebooks de NotebookLM usando el token [TU_TOKEN]"*. 
Ejecutaré el script `scripts/nlm_client.py --action list --token [TU_TOKEN]`.

### 2. Leer Contenido de un Notebook
Pídeme: *"Lee el contenido del notebook con ID [ID_DEL_NOTEBOOK] usando el token [TU_TOKEN]"*.
Esto me dará acceso a tus fuentes (Sources) y notas guardadas.

### 3. Generar Artículos
Una vez que tenga el contenido, pídeme: *"Genera un artículo sobre [TEMA]"*.
- Consultaré `references/article_patterns.md` para elegir la estructura.
- Usaré tus datos de NotebookLM como base para el contenido.

## ⚠️ Notas de Seguridad
- El token `__Host-GAPS` es personal y da acceso a tu sesión. 
- No lo compartas públicamente ni lo subas a repositorios.
- La skill usa la librería `notebooklm-py` para la conexión.
