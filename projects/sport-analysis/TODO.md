- CLI

- Esporta features anche per half marathon:
   - aggiungi plot pace per km al Fosso?

- plot_half_marathon_api.py
  - hr histogram tot, con indicaz di avg, min, max
  - velocita con moving average e magari linea verticale coi tempi ogni 5 km
  - hr con moving average e linea verticale con media ogni 5 km
  - confronto con un'attivita preimpostata e magari la precedente gara HM
    che cerca su strava e chiede conferma in modo interattivo

- strava-client: stesa cosa che ho fatto in garmin: ensure data coherent
- notebook: finisci compare_avg_hr_in_strava_vs_garmin_vs_computed()
   e plot_hr_histogram()

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
