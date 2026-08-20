- plot.plot_ride_api.test_plot_climb_ride_api.TestPlotClimbRideApi.test_111

- committa tutto!!!!!!!!!!!

- aggiorna appunti su VCR.py in prod code e Relative imports
- add calendar sketch (and use proper vcr.py)

- scritta semplice: rimuovi MA(pace)
- sotto le barre orizzontale delle HR zone scrivere tutte le perc:
  Z0 1%, Z1 3%, ...
- invece di usare immagini che creo io a mano in plot (come plot_interval_1000m_run_api.png)
   fare si che il test_happy_flow crei quell'immagine in modo che sia aggiornata
   dopo ogni cambiamento
- replace get_string_from_env() e override_settings in settings_module.py con settings_utils lib
- activity_id: strava-* or garmin-*
- UserWarning: Attempt to set non-positive xlim on a log-scaled axis will be ignored.
- usa domande interattive
  vedi `search_strava_api_cli.py`
- 1 chart largo sopra con i tempi
  3 sotto piccoli
  non rosso, ma violetto

- usa ConsoleAdapterMock() come in test_search_strava_api_cmd.py?





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
- san search-matching-activity --stravaid=<id> (invece di search-matching-strava-activity)
- san search-db <text> (invece di db-search-text)
- san get-activity-strava <id> (NEW)
- san get-segment-strava <id>|selvino|stelvio  (NEW)
- san get-activity-garmin <id> (NEW)

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
