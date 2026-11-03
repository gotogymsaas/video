# Animación QAF: trayectorias y revelación sincronizada

Dos manuscritos de Juan Manuel Goenaga Castro, con referencias clásicas ejecutables.
No se declara ventaja cuántica, generación neuronal ni calidad perceptual validada.

## Configuración

En un shot de cualquiera de los dos renderers:

```json
{"motion":{"keyframes":[
  {"at":0,"focus":[0.4,0.5],"zoom":1},
  {"at":0.6,"focus":[0.6,0.45],"zoom":1.15},
  {"at":1,"focus":[0.6,0.45],"zoom":1.15}
]}}
```

En el compositor estándar, asociar `nodes` a índices de `subtitles` medidos:

```json
{"start":0,"end":8,"nodes":["Evidencia","Análisis"],"node_cues":[0,1]}
```

Los cues deben comenzar dentro del plano y conservar el orden. El director debe
comprobar que la relación semántica sea correcta. No se estiman tiempos de voz.

Validación dirigida: `python -m unittest tests.test_animation tests.test_mathematics tests.test_cinema tests.test_relational_planner -v`.

Cambios opcionales: proyectos existentes no necesitan nuevos campos. La ruta
estándar utiliza ahora un recorte seguro compartido; ambas salidas deben revisarse.
Los nodos y enlaces pertenecen al compositor estándar, no a Film.context_graph.

## Ejecución de regresión

`python -m unittest discover -s tests -q`: 168 pruebas, OK, 5 omitidas.
Las omisiones corresponden a compuertas existentes de entorno. Advertencias de
recursos en pruebas de video preexistentes no constituyen revisión editorial.
No se ejecutó estudio perceptual ni se generó una nueva versión del episodio.
