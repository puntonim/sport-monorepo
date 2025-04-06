**Sport monorepo**
==================

Just a collection of Sport software I happened to write.

There are 2 categories of software:
- `libs`: eg. `libs/strava-client`. They are standalone Python libs that can be
 installed individually. Projects in this sport-monorepo typically include some of
 them as local requirements. Other projects can install them from the Git subdir.
- `projects`: eg. `projects/strava-facade-api`. They are deployed either as (a set of)
 Lambdas or cli or Docker images. Some of their requirements are local libs.


Copyright
=========

---

Copyright puntonim (https://github.com/puntonim). No License.
