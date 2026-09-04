
- aggiungi l'HR al grafico sopra di simple-run
  Con l'opzione --no-hr-in-pace-chart (default fale) per rimuoverlo
   e con default true quando ci sono comparison

- Infine usa il nuovo ACTIVITY_ID_PARAM_TYPE in tutti i comandi che ora usano LATEST
  Commit

- move base_plot.make_png_file_path() to utils/file_system_utils

- UserWarning: Attempt to set non-positive xlim on a log-scaled axis will be ignored.
  in interval run

- in climb ride aggiungi 2 args:
    --no-zones-boundaries-in-hr-hist
    --no-time-in-hr-hist
  to solve the overlapping labels (see plot_climb_ride_api.png)

- usa ConsoleAdapterMock() come in test_search_strava_api_cmd.py?
- san print-activity strava-123
  console print summary e details

- Unire piu comandi:
    plot-run: che unisce plot-simple-run, plot-interval-run
    plot-ride: che unisce plot-climb-ride, plot-simple-ride

- in tutti i plot, metti distance su asse x basso (gia fatto in run, non i ride)
   e time su asse x alto


EOY feature
- add "per week" data
- controlla se i PR per la corsa e bici sono giusti
- HR max per sport
   Mean e std-err del top 10% e 5% HR del top 10% di attività ordinate per HR max
- aggiungi emoji tipo trophy per PR e bike per Ride e heart per HR?
    https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.figimage.html
    https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open
    https://stackoverflow.com/questions/3609585/how-to-insert-a-small-image-on-the-corner-of-a-plot-with-matplotlib
- avg weight per month, and diff peso finale - peso iniziale con g/month
- non dve essere un cli, perche ci sono cose da fare a mano o ad hoc,
   es i PR di powerlifting che non possono essere estratti da garmin o strava
- quindi forse meglio fare dei files tipo:
  - base_eoy_recap_api.py
    eoy_recap_2025_api.py
    eoy_recap_2024_api.py
- cancella branch eoy e eoy-new

REFACTORING
- san search-db <text> (invece di db-search-text)
- san get-segment-strava <id>|selvino|stelvio  (NEW)

SEARCH CLI per trovare il migliore 10km|HM (run)
- cerco le corse di almeno 10km
- prendo le prime 5 per passo medio
- chiedo activity details e vedo il best_efforts sui 10km 

SEARCH CLI per trovare i migliori 300m (run)
- posso cercare in garmin quando ho fatto quel workout
- e pure in strava per titolo
- estraggo i tempi, come faccio nel plot

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
