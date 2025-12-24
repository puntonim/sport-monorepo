SEARCH CLI per trovare il migliore segmento selvino (ride)
- strava-client: aggiungi tutti i possibili filtri alla cli
- poi aggiungili qui
- --no-logs??
- sistema per bene gli output su stdout/stderr

- san search-matching-activity --stravaid=......
- san search-db text
- san get-activity-strava <id>
- san get-segment-strava <id>|selvino|stelvio
- san get-activity-garmin <id>

SEARCH CLI per trovare il migliore 10km|HM (run)
- cerco le corse di almeno 10km
- prendo le prime 5 per passo medio
- chiedo activity details e vedo il best_efforts sui 10km 

SEARCH CLI per trovare i migliori 300m (run)
- posso cercare in garmin quando ho fatto quel workout
- e pure in strava per titolo
- estraggo i tempi, come faccio nel plot

EOY feature
- add "per week" data
- avg weight per month, and diff peso finale - peso iniziale con g/month
- delete sketches/gis_utils....
- non dve essere un cli, perche ci sono cose da fare a mano o ad hoc,
   es i PR di powerlifting che non possono essere estratti da garmin o strava
- quindi forse meglio fare dei files tipo:
  - base_eoy_recap_api.py
    eoy_recap_2025_api.py
    eoy_recap_2024_api.py
