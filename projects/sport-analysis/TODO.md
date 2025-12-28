SEARCH CLI per trovare il migliore segmento selvino (ride)
- arg per aggiungere se avevo fascia cardio o no

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
- torna sul branch eoy-new e pull --rebase
- add "per week" data
- avg weight per month, and diff peso finale - peso iniziale con g/month
- delete sketches/gis_utils....
- non dve essere un cli, perche ci sono cose da fare a mano o ad hoc,
   es i PR di powerlifting che non possono essere estratti da garmin o strava
- quindi forse meglio fare dei files tipo:
  - base_eoy_recap_api.py
    eoy_recap_2025_api.py
    eoy_recap_2024_api.py


=================

- Usa le nuove feature di datetime_utils in strava_client e garmin_client
   e rinomina tutto in start_date_after|before e start_day_after|before

- rename `count` dir to `stats|generic_stats|misc_stats|basic_stats|other_stats`?
  and use it as a container of anything that does not fit in other dirs?

- aggiungi plot pace per km al Fosso?

- plot_half_marathon_api.py
  - hr histogram tot, con indicaz di avg, min, max
  - velocita con moving average e magari linea verticale coi tempi ogni 5 km
  - hr con moving average e linea verticale con media ogni 5 km
  - confronto con un'attivita preimpostata e magari la precedente gara HM
    che cerca su strava e chiede conferma in modo interattivo

- strava-client: stesa cosa che ho fatto in garmin: ensure data coherent

- aggiungi tests per le fz esistenti e get rid of notebook file 

- strava client: ho fatto tt le modifiche richiesta in qs notebook?
- strava client: committalo

- strava client: aggiornalo in tutti i progetti che lo usano e committali
  - cambiamento: strava token managers
  - cambiamento: tutte le risposte come oggetti

- strava tags manager:
  - per ogni nuova attivita (webhook from strava)
  - mi manda un link via email/telegram
  - che apre una webpage che mi fa scegliere i tag
  - e poi li scrive su strava
  - aggiunge anche la corrispondete attivita garmin

- estrai peso da bilancia e aggiungilo come tag a strava
- estrai sleep score da garmin e aggiungilo come tag a strava
